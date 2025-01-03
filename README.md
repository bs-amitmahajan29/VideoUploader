# Video Uploader FastAPI Application

This repository contains a FastAPI application for managing video uploads, trimming, sharing, and merging. The application uses SQLite as the database and OpenCV for video processing. The system includes authentication via API tokens passed by headers.

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Setup and Installation](#setup-and-installation)
4. [Running the Application](#running-the-application)
5. [Running the Tests](#running-the-tests)
6. [API Endpoints](#api-endpoints)
7. [Folder Structure](#folder-structure)
8. [Configuration](#configuration)
9. [Citation and References](#citation-and-references)

## Features

- **Video Upload**: Upload video files within defined size and duration limits.
- **Video Trimming**: Trim videos based on start and end times.
- **Video Sharing**: Generate shareable links with expiry for downloading videos.
- **Video Merging**: Merge multiple video files into one.
- **Authentication**: Secure APIs using token-based authentication.

## Requirements

- Python version: `3.9.6`
- Virtual environment name: `video_uploader_env`

## Setup and Installation

### Step 1: Clone the Repository
```bash
git clone <repository_url>
cd <repository_folder>
```

### Step 2: Create and Activate Virtual Environment
```bash
python3 -m venv video_uploader_env
source video_uploader_env/bin/activate  # On Windows: video_uploader_env\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Configuration
1. Navigate to the `config` folder.
2. Update the `config.json` file with your desired settings:
   ```json
   {
       "api_token": ["token1", "token2"],
       "upload_directory": "uploads",
       "db_file": "video_uploader.db",
       "max_size_bytes": 50000000,
       "min_duration_sec": 1,
       "max_duration_sec": 300,
       "share_file_expiry_sec": 3600
   }
   ```

### Step 5: Initialize Database
The database is automatically initialized on application start.

## Running the Application

Start the FastAPI server:
```bash
fastapi dev video_uploader.py
```

By default, the application runs on `http://127.0.0.1:8000`.

## Running the Tests

Return `True` from `def authenticate(api_token: str = Header(None)):` in `video_uploader.py`. (This is because I haven't yet been able to mock this function run)
Post that run:
```bash
pytest --cov
```

Coverage Results
```
---------- coverage: platform darwin, python 3.9.6-final-0 -----------
Name                     Stmts   Miss  Cover
--------------------------------------------
__init__.py                  0      0   100%
test_video_uploader.py      78      0   100%
video_uploader.py          199     20    90%
--------------------------------------------
TOTAL                      277     20    93%
```

## API Endpoints

### Authentication
- **Check API Token**: `POST /check_api_token`

### Video Operations
- **Upload Video**: `POST /upload`
- **Trim Video**: `POST /trim`
- **Merge Videos**: `POST /merge`
- **Share Video**: `POST /share`
- **Download Video**: `GET /download/{link_id}`

### API Playground
- Use /docs endpoint after starting the server for trying out APIs

## Folder Structure
```
VideoUploader/
├── config/                      # Stores config files
│   └── config.json
|   └── video_uploader.db
├── uploads/                     # Stores uploaded and processed video files
├── video_uploader.py            # Main application file
└── requirements.txt             # Dependency list
```

## Configuration

The `config/config.json` file contains application settings. Key options:

- `api_token`: List of valid tokens for authentication.
- `upload_directory`: Path to store uploaded and processed videos.
- `db_file`: SQLite database file path.
- `max_size_bytes`: Maximum allowed file size in bytes.
- `min_duration_sec`: Minimum allowed video duration in seconds.
- `max_duration_sec`: Maximum allowed video duration in seconds.
- `share_file_expiry_sec`: Default expiry time for shared links in seconds.

---

## Citation and References

Below references were used in the project

- https://fastapi.tiangolo.com/
- https://www.geeksforgeeks.org/opencv-python-tutorial/
- https://stackoverflow.com/questions/60716529/download-file-using-fastapi
- https://www.geeksforgeeks.org/python-writing-to-video-with-opencv/
- https://www.geeksforgeeks.org/get-video-duration-using-python-opencv/
- https://karobben.github.io/2021/04/10/Python/opencv-v-paste/
