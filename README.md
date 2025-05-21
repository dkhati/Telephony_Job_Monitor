# Telephony Job Scheduler Service

A microservice for scheduling and processing outbound call jobs with real-time status updates via WebSocket.

## Features

- REST API for scheduling call jobs
- Background worker for processing jobs
- WebSocket endpoint for real-time job status updates
- SQLite database for job persistence
- Docker containerization

## Prerequisites

- Docker
- Python 3.11+ (for local development)

## Running with Docker

1. Make sure you have all the required files in your project directory:
```
your_project_directory/
├── main.py
├── job_processor.py
├── requirements.txt
├── Dockerfile
└── static/
    ├── index.html
    └── websocket_test.html
```

2. Build the Docker image:
```bash
docker build -t telephony-scheduler .
```

3. Run the Docker container:
```bash
docker run -p 8000:8000 -p 8001:8001 telephony-scheduler
```

4. Access the application:
   - Main Interface: `http://localhost:8000`
   - WebSocket Test Interface: `http://localhost:8000/ws-test`

### Additional Docker Commands

Run container in background:
```bash
docker run -d -p 8000:8000 -p 8001:8001 telephony-scheduler
```

Stop the container:
```bash
# Find the container ID
docker ps

# Stop the container
docker stop <container_id>
```

View container logs:
```bash
docker logs <container_id>
```

## Testing the Application

1. Open both interfaces in separate browser tabs:
   - Main interface: `http://localhost:8000`
   - WebSocket test: `http://localhost:8000/ws-test`

2. In the main interface:
   - Enter a phone number (e.g., "+1234567890")
   - Enter a message
   - Click "Create Job"

3. Watch the WebSocket test interface for real-time updates showing:
   - Job creation
   - Status changes (PENDING → PROCESSING → COMPLETED)
   - Timestamps for each update

## API Endpoints

### Schedule a Job
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Hello from the scheduler!",
    "scheduled_time": "2024-01-01T12:00:00Z"  # Optional
  }'
```

### Get Job Status
```bash
curl http://localhost:8000/jobs/{job_id}
```

### WebSocket Connection
Connect to `ws://localhost:8000/ws/jobs` to receive real-time job status updates.

## Job Status Flow

1. `PENDING`: Initial state when job is created
2. `PROCESSING`: Job is being processed
3. `COMPLETED`: Job successfully processed
4. `FAILED`: Job processing failed

## Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn main:app --reload
```

## Architecture

- FastAPI for HTTP and WebSocket endpoints
- SQLAlchemy with aiosqlite for async database operations
- Background task processing with asyncio
- WebSocket broadcasting for real-time updates

## Error Handling

- Automatic retries for failed jobs
- Detailed error logging
- Graceful error handling for WebSocket connections
- Database transaction management 