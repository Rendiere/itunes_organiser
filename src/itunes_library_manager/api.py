from fastapi import FastAPI, Depends, WebSocket, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import get_db, create_tables
from .models import Track
from .schemas import TrackCreate, TrackUpdate, TrackResponse
from .tasks import infer_year, parse_xml
import json
import asyncio
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = f"uploaded_{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    task = parse_xml.delay(file_path)
    return {"task_id": str(task.id)}

@app.get("/tracks", response_model=List[TrackResponse])
def get_tracks(db: Session = Depends(get_db)):
    tracks = db.query(Track).all()
    return tracks

@app.post("/infer_year/{track_id}")
async def start_year_inference(track_id: int):
    task = infer_year.delay(track_id)
    return {"task_id": str(task.id)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        task_id = await websocket.receive_text()
        task = parse_xml.AsyncResult(task_id)
        while not task.ready():
            if task.info and 'progress' in task.info:
                await websocket.send_json({"progress": task.info['progress']})
            await asyncio.sleep(1)
        result = task.get()
        await websocket.send_json({"status": "completed", "tracks_created": result['tracks_created']})

# Add this function to clear the database
@app.on_event("shutdown")
async def clear_database():
    db = next(get_db())
    db.query(Track).delete()
    db.commit()