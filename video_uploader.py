from fastapi import FastAPI, File, UploadFile, HTTPException, Header
import os
import json

with open('config/config.json') as config_file:
    config = json.load(config_file)

API_TOKENS = config['api_token']

UPLOAD_FOLDER = 'uploads'
DB_FILE = 'config/video_uploader.db'

# Initialize app
app = FastAPI()
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def authenticate(api_token: str = Header(None)):
    if not api_token:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing api_token")
    if api_token not in API_TOKENS:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API token")
    return True

@app.post("/check_api_token")
async def check_api_token(api_token: str = Header(None)):
    authorized = authenticate(api_token)
    return {"Authorized": authorized}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...), api_token: str = Header(None)):
    authenticate(api_token)

    await file.seek(0)
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    return {"filename": filename}
