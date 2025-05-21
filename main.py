from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
from datetime import datetime
import uvicorn
from job_processor import JobProcessor, Job, JobStatus
import os

app = FastAPI(title="Telephony Job Scheduler")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


os.makedirs("static", exist_ok=True)


app.mount("/static", StaticFiles(directory="static"), name="static")


job_processor = JobProcessor()

class JobRequest(BaseModel):
    phone_number: str
    message: str
    scheduled_time: Optional[datetime] = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/ws-test")
async def read_ws_test():
    return FileResponse("static/websocket_test.html")

@app.post("/jobs")
async def create_job(job_request: JobRequest):
    job = await job_processor.create_job(
        phone_number=job_request.phone_number,
        message=job_request.message,
        scheduled_time=job_request.scheduled_time
    )
    return {"job_id": job.id, "status": job.status}

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = await job_processor.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.websocket("/ws/jobs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_job_updates():
    while True:
        job_update = await job_processor.get_job_update()
        if job_update:
            await manager.broadcast(json.dumps(job_update))
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(job_processor.process_jobs())
    asyncio.create_task(broadcast_job_updates())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 