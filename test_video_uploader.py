import os
import pytest
from fastapi.testclient import TestClient
from .video_uploader import app, UPLOAD_FOLDER, DB_FILE, config, authenticate

client = TestClient(app)

def setup_module(module):
    """Set up the test environment before running tests."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    
    # Re-initialize the database
    from .video_uploader import init_db
    init_db()

def teardown_module(module):
    """Clean up after tests."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    if os.path.exists(UPLOAD_FOLDER):
        for file in os.listdir(UPLOAD_FOLDER):
            os.remove(os.path.join(UPLOAD_FOLDER, file))

@pytest.fixture
def api_token():
    """Provide a valid API token for authentication."""
    return config['api_token'][0]

def test_upload_video(api_token):
    video_path = "sample_data/video1.mp4"
    with open(video_path, "rb") as video_file:
        response = client.post(
            "/upload",
            files={"file": ("video1.mp4", video_file, "video/mp4")},
            headers={"api_token": api_token}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "video_id" in data
    assert "filename" in data

def test_trim_video(api_token):
    video_path = "sample_data/video1.mp4"
    with open(video_path, "rb") as video_file:
        upload_response = client.post(
            "/upload",
            files={"file": ("video1.mp4", video_file, "video/mp4")},
            headers={"api_token": api_token}
        )
    
    video_id = upload_response.json()["video_id"]

    # Trim video
    trim_response = client.post(
        "/trim",
        json={"video_id": video_id, "start_time": 1.0, "end_time": 3.0},
        headers={"api_token": api_token}
    )

    assert trim_response.status_code == 200
    trim_data = trim_response.json()
    assert "video_id" in trim_data
    assert "filename" in trim_data

def test_trim_video_invalid_end_time(api_token):
    video_path = "sample_data/video1.mp4"
    with open(video_path, "rb") as video_file:
        upload_response = client.post(
            "/upload",
            files={"file": ("video1.mp4", video_file, "video/mp4")},
            headers={"api_token": api_token}
        )
    
    video_id = upload_response.json()["video_id"]

    # Trim video with invalid end_time
    trim_response = client.post(
        "/trim",
        json={"video_id": video_id, "start_time": 1.0, "end_time": 100000000.0},
        headers={"api_token": api_token}
    )

    assert trim_response.status_code == 400
    assert "end_time" in trim_response.json()["detail"]

def test_merge_videos(api_token):
    video_path = "sample_data/video1.mp4"
    video_ids = []

    # Upload multiple videos
    for _ in range(2):
        with open(video_path, "rb") as video_file:
            upload_response = client.post(
                "/upload",
                files={"file": ("video1.mp4", video_file, "video/mp4")},
                headers={"api_token": api_token}
            )
            video_ids.append(upload_response.json()["video_id"])

    # Merge videos
    merge_response = client.post(
        "/merge",
        json={"video_ids": video_ids},
        headers={"api_token": api_token}
    )

    assert merge_response.status_code == 200
    merge_data = merge_response.json()
    assert "video_id" in merge_data
    assert "filename" in merge_data

def test_share_video(api_token):
    video_path = "sample_data/video1.mp4"
    with open(video_path, "rb") as video_file:
        upload_response = client.post(
            "/upload",
            files={"file": ("video1.mp4", video_file, "video/mp4")},
            headers={"api_token": api_token}
        )

    video_id = upload_response.json()["video_id"]

    # Share video
    share_response = client.post(
        "/share",
        json={"video_id": video_id, "expiry_sec": 3600},
        headers={"api_token": api_token}
    )

    assert share_response.status_code == 200
    share_data = share_response.json()
    assert "link_id" in share_data
    assert "expires_at" in share_data

def test_download_video(api_token):
    video_path = "sample_data/video1.mp4"
    with open(video_path, "rb") as video_file:
        upload_response = client.post(
            "/upload",
            files={"file": ("video1.mp4", video_file, "video/mp4")},
            headers={"api_token": api_token}
        )

    video_id = upload_response.json()["video_id"]

    # Share video
    share_response = client.post(
        "/share",
        json={"video_id": video_id, "expiry_sec": 3600},
        headers={"api_token": api_token}
    )

    link_id = share_response.json()["link_id"]

    # Download video
    download_response = client.get(f"/download/{link_id}")

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "video/mp4"
