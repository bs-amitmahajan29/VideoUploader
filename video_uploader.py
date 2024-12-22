from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from pydantic import BaseModel
import os
import uuid
import json
import sqlite3
from datetime import datetime
import cv2

with open('config/config.json') as config_file:
    config = json.load(config_file)

API_TOKENS = config['api_token']

UPLOAD_FOLDER = 'uploads'
DB_FILE = 'config/video_uploader.db'

# Initialize app
app = FastAPI()
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database setup
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def authenticate(api_token: str = Header(None)):
    if not api_token:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing api_token")
    if api_token not in API_TOKENS:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API token")
    return True

class TrimRequest(BaseModel):
    video_id: str
    start_time: float = 0
    end_time: float = None

@app.post("/check_api_token")
async def check_api_token(api_token: str = Header(None)):
    authorized = authenticate(api_token)
    return {"Authorized": authorized}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...), api_token: str = Header(None)):
    authenticate(api_token)

    file_size = len(await file.read())
    if file_size > config['max_size_bytes']:
        raise HTTPException(status_code=400, detail="File size exceeds the allowed limit")

    await file.seek(0)
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())
    
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        os.remove(filepath)
        raise HTTPException(status_code=400, detail="Invalid video file")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    cap.release()

    if duration < config['min_duration'] or duration > config['max_duration']:
        os.remove(filepath)
        raise HTTPException(status_code=400, detail="Video duration is out of allowed range")
    
    video_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO videos (id, filename, created_at, updated_at) VALUES (?, ?, ?, ?)',
                   (video_id, filename, datetime.now(), datetime.now()))
    conn.commit()
    conn.close()

    return {"video_id": video_id, "filename": filename}

@app.post("/trim")
async def trim_video(request: TrimRequest, api_token: str = Header(None)):
    authenticate(api_token)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename FROM videos WHERE id = ?', (request.video_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Video not found")

    filename = result[1]
    video_id = result[0]
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Invalid video file")

    fps = cap.get(cv2.CAP_PROP_FPS)
    start_frame = int(request.start_time * fps)
    end_time = request.end_time or (cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps)
    end_frame = int(end_time * fps)

    trimmed_filename = f"trimmed_{filename}"
    trimmed_filepath = os.path.join(UPLOAD_FOLDER, trimmed_filename)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(trimmed_filepath, fourcc, fps, (
        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ))
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame_count > end_frame:
            break
        if frame_count >= start_frame:
            out.write(frame)
        frame_count += 1
    cap.release()
    out.release()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE videos SET filename = ?, updated_at = ? WHERE id = ?',
                   (trimmed_filename, datetime.now(), video_id))
    conn.commit()
    conn.close()
    os.remove(filepath)

    return {"video_id": video_id, "filename": trimmed_filename}
