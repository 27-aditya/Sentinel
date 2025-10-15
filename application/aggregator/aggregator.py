import os
import time
import subprocess
import threading
import datetime
from pathlib import Path
import asyncio
from typing import List

import psycopg2
import cv2
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware  

from db_redis.sentinel_redis_config import *
from modules.aggregator_engine import ResultAggregator

# Import all route modules
from routes import websocket_routes, vehicle_routes, stream_routes, file_browser_routes

# Global ready flag (using dict to allow mutation in routes)
SYSTEM_READY = {"ready": False}

# Location
LOCATION = os.getenv("LOCATION", "DEFAULT_LOCATION")
print("Location: " + LOCATION)

# RTSP url
RTSP_URL = os.getenv("RTSP_STREAM")
if not RTSP_URL:
    print("Error: RTSP_STREAM not set in environment variables.")
    exit(1)

# Database Connection
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASS]):
    print("Error: Database environment variables missing.")
    exit(1)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    
# WebSocket Connection Manager 
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

# A global instance of the manager 
manager = ConnectionManager()

# RTSP viewer
def generate_frames():
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        print("Could not connect to RTSP stream")
        return

    while True:
        success, frame = cap.read()
        if not success:
            time.sleep(0.1)
            continue
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )

# TEMP RTSP TO HLS CONVERSION - REMOVE
def start_hls_conversion():
    """Convert RTSP to HLS using FFmpeg with browser-compatible settings"""
    output_file = HLS_OUTPUT_DIR / "stream.m3u8"
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",  # Use TCP for more reliable RTSP
        "-i", RTSP_URL,
        
        # Video encoding - Re-encode to H.264 (browser compatible)
        "-c:v", "libx264",
        "-preset", "veryfast",  # Fast encoding
        "-tune", "zerolatency",  # Low latency for live streaming
        "-profile:v", "baseline",  # Maximum browser compatibility
        "-level", "3.0",
        "-g", "30",  # GOP size (keyframe interval)
        "-sc_threshold", "0",  # Disable scene change detection
        
        # Video quality
        "-b:v", "2000k",  # 2 Mbps bitrate
        "-maxrate", "2000k",
        "-bufsize", "4000k",
        
        # Audio encoding
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",  # Sample rate
        
        # HLS settings
        "-f", "hls",
        "-hls_time", "2",  # 2-second segments
        "-hls_list_size", "5",  # Keep 5 segments in playlist
        "-hls_flags", "delete_segments+append_list",  # Delete old segments
        "-hls_segment_type", "mpegts",  # Use MPEG-TS container
        "-start_number", "1",
        
        # Output
        str(output_file)
    ]
    
    print(f"Starting HLS conversion: {output_file}")
    
    process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    return process

# File Browser Integration
BASE_DIR = Path(__file__).resolve().parent
WEB_ROOT = BASE_DIR / "web"
STATIC_PATH = WEB_ROOT / "static"
TEMPLATES_PATH = WEB_ROOT / "templates"

# TEMP HSL STREAM
HLS_OUTPUT_DIR = STATIC_PATH / "hls_stream"
HLS_OUTPUT_DIR.mkdir(exist_ok=True)

# Make sure directories exist
WEB_ROOT.mkdir(exist_ok=True)
STATIC_PATH.mkdir(exist_ok=True)
LOCATION_PATH = STATIC_PATH / LOCATION
LOCATION_PATH.mkdir(parents=True, exist_ok=True)
TEMPLATES_PATH.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_PATH))

# Initialize route modules with dependencies
websocket_routes.init_globals(SYSTEM_READY, manager)
vehicle_routes.init_db(get_db_connection)
stream_routes.init_stream(generate_frames, templates, LOCATION, HLS_OUTPUT_DIR)
file_browser_routes.init_file_browser(STATIC_PATH, templates, LOCATION)

# FastAPI Setup
app = FastAPI(title="Sentinel Vehicle API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

# Include all routers
app.include_router(websocket_routes.router)
app.include_router(vehicle_routes.router)
app.include_router(stream_routes.router)
app.include_router(file_browser_routes.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    
    # Pass db connection function to aggregator
    aggregator = ResultAggregator(manager, loop, get_db_connection)
    
    # Start aggregator in background thread
    aggregator_thread = threading.Thread(target=aggregator.process_results, daemon=True)
    aggregator_thread.start()
    
    # TEMP - REMOVE LATER Start HLS conversion
    hls_thread = threading.Thread(target=start_hls_conversion, daemon=True)
    hls_thread.start()

    print("Aggregator background thread has been scheduled.")

# Entrypoint 
if __name__ == "__main__":
    import uvicorn
    print("Starting Sentinel Aggregator Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
