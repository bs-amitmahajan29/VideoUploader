# Video Uploader FastAPI Application

This repository contains a FastAPI application for managing video uploads, trimming, sharing, and merging. The application uses SQLite as the database and OpenCV for video processing. The system includes authentication via API tokens passed by headers.

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Setup and Installation](#setup-and-installation)
4. [Running the Application](#running-the-application)
5. [API Endpoints](#api-endpoints)
6. [Folder Structure](#folder-structure)
7. [Configuration](#configuration)

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
