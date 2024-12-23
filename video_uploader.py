from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
import json
import sqlite3
from datetime import datetime, timedelta
import cv2

with open('config/config.json') as config_file:
    config = json.load(config_file)

API_TOKENS = config['api_token']
UPLOAD_FOLDER = config['upload_directory']
DB_FILE = config['db_file']

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_links (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY(video_id) REFERENCES videos(id)
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

class ShareRequest(BaseModel):
    video_id: str
    expiry_sec: int = config['share_file_expiry_sec']

class MergeRequest(BaseModel):
    video_ids: list

@app.post("/check_api_token")
async def check_api_token(api_token: str = Header(None)):
    authorized = authenticate(api_token)
    return {"Authorized": authorized}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...), api_token: str = Header(None)):
    authenticate(api_token)

    file_size = len(await file.read())
    if file_size > config['max_size_bytes']:
        raise HTTPException(status_code=400, detail=f"File size exceeds the allowed limit of {config['max_size_bytes']} bytes")

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

    if duration < config['min_duration_sec'] or duration > config['max_duration_sec']:
        os.remove(filepath)
        raise HTTPException(status_code=400, detail=f"Video duration between {config['min_duration_sec']}s to {config['max_duration_sec']}s are only allowed")
    
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
        raise HTTPException(status_code=404, detail=f"Video {request.video_id} not found")

    filename = result[1]
    video_id = result[0]
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail=f"Invalid video ({request.video_id}) file")

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

@app.post("/share")
async def share_video(request: ShareRequest, api_token: str = Header(None)):
    authenticate(api_token)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT filename FROM videos WHERE id = ?', (request.video_id,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=f"Video {request.video_id} not found")

    link_id = str(uuid.uuid4())
    now_time = datetime.now()
    expires_at = now_time + timedelta(seconds=request.expiry_sec)
    cursor.execute('INSERT INTO shared_links (id, video_id, created_at, expires_at) VALUES (?, ?, ?, ?)',
                   (link_id, request.video_id, now_time, expires_at))
    conn.commit()
    conn.close()

    return {"video_id": request.video_id, "expires_at": expires_at, "link_id": link_id}

@app.get("/download/{link_id}")
async def download_video(link_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT video_id, expires_at FROM shared_links WHERE id = ?', (link_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail=f"Link {link_id} not found")

    video_id, expires_at = result
    if datetime.now() > datetime.fromisoformat(expires_at):
        raise HTTPException(status_code=410, detail=f"Link {link_id} has expired at {datetime.fromisoformat(expires_at)}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT filename FROM videos WHERE id = ?', (video_id,))
    video_result = cursor.fetchone()
    conn.close()

    if not video_result:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    filename = video_result[0]
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    return FileResponse(filepath, filename=filename)

@app.post("/merge")
async def merge_videos(request: MergeRequest, api_token: str = Header(None)):
    authenticate(api_token)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    filenames = []
    for video_id in request.video_ids:
        cursor.execute('SELECT filename FROM videos WHERE id = ?', (video_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail=f"Video with id {video_id} not found")
        filenames.append(result[0])
    conn.close()

    video_id = uuid.uuid4()
    merged_filename = f"merged_{video_id.hex}.mp4"
    merged_filepath = os.path.join(UPLOAD_FOLDER, merged_filename)

    first_cap = cv2.VideoCapture(os.path.join(UPLOAD_FOLDER, filenames[0]))
    fps = first_cap.get(cv2.CAP_PROP_FPS)
    width = int(first_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(first_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    first_cap.release()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(merged_filepath, fourcc, fps, (width, height))

    for filename in filenames:
        cap = cv2.VideoCapture(os.path.join(UPLOAD_FOLDER, filename))
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        cap.release()

    out.release()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO videos (id, filename, created_at, updated_at) VALUES (?, ?, ?, ?)',
                   (str(video_id), merged_filename, datetime.now(), datetime.now()))
    conn.commit()
    conn.close()

    return {"video_id": str(video_id), "filename": merged_filename}
