from enum import Enum
from datetime import datetime
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.future import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./jobs.db"
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    phone_number = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_time = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class JobProcessor:
    def __init__(self):
        self.job_updates = asyncio.Queue()
        self.max_retries = 3

    async def init_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def create_job(self, phone_number: str, message: str, scheduled_time: Optional[datetime] = None) -> Job:
        job = Job(
            id=str(uuid.uuid4()),
            phone_number=phone_number,
            message=message,
            scheduled_time=scheduled_time
        )
        
        async with async_session() as session:
            session.add(job)
            await session.commit()
            await session.refresh(job)

            await self.job_updates.put({
                "job_id": job.id,
                "status": job.status,
                "type": "created"
            })
            
            return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        async with async_session() as session:
            result = await session.execute(select(Job).where(Job.id == job_id))
            return result.scalar_one_or_none()

    async def update_job_status(self, job_id: str, status: JobStatus) -> Optional[Job]:
        async with async_session() as session:
            job = await self.get_job(job_id)
            if job:
                job.status = status
                job.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(job)
                
                await self.job_updates.put({
                    "job_id": job.id,
                    "status": job.status,
                    "type": "updated"
                })
                
                return job
            return None

    async def get_job_update(self) -> Optional[Dict[str, Any]]:
        try:
            return await self.job_updates.get()
        except asyncio.QueueEmpty:
            return None

    async def process_jobs(self):
        await self.init_db()
        while True:
            try:
                async with async_session() as session:

                    now = datetime.utcnow()
                    result = await session.execute(
                        select(Job).where(
                            Job.status == JobStatus.PENDING,
                            (Job.scheduled_time <= now) | (Job.scheduled_time == None)
                        )
                    )
                    jobs = result.scalars().all()

                    for job in jobs:
                        await self.process_job(job)

            except Exception as e:
                logger.error(f"Error processing jobs: {str(e)}")

            await asyncio.sleep(1)

    async def process_job(self, job: Job):
        try:

            await self.update_job_status(job.id, JobStatus.PROCESSING)
            
            # Simulate Twilio API call
            logger.info(f"Simulating call to {job.phone_number} with message: {job.message}")
            await asyncio.sleep(2)
            

            await self.update_job_status(job.id, JobStatus.COMPLETED)
            
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {str(e)}")
            await self.update_job_status(job.id, JobStatus.FAILED) 