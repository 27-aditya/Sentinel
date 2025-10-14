import os
import time
import threading
import datetime
from collections import defaultdict
from pathlib import Path
import asyncio
import json
from typing import List

import psycopg2
import cv2
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db_redis.sentinel_redis_config import *

# Global ready flag
SYSTEM_READY = False

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
        print("❌ Could not connect to RTSP stream")
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

# Aggregator Class
class ResultAggregator:
    # MODIFIED: __init__ now accepts the manager and the event loop
    def __init__(self, manager: ConnectionManager, loop: asyncio.AbstractEventLoop):
        self.pending_jobs = defaultdict(dict)  # job_id -> {worker: result}
        self.r = get_redis_connection()
        self.manager = manager
        self.loop = loop

    def construct_keyframe_url(self, vehicle_id, location):
        """Construct keyframe URL from vehicle_id and location"""
        try:
            # Extract date from vehicle_id: uuid_YYYYMMDD_HHMMSS_type_location
            parts = vehicle_id.split('_')
            if len(parts) >= 2:
                date_part = parts[1]
                formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                
                # Construct URL: http://localhost:8000/static/LOCATION/DATE/keyframes/VEHICLE_ID.jpg
                keyframe_url = f"http://localhost:8000/static/{location}/{formatted_date}/keyframes/{vehicle_id}.jpg"
                return keyframe_url
            return None
        except Exception as e:
            print(f"Error constructing keyframe URL for {vehicle_id}: {e}")
            return None

    def construct_plate_url(self, vehicle_id, location):
        """Construct plate image URL from vehicle_id and location"""
        try:
            # Extract date from vehicle_id: uuid_YYYYMMDD_HHMMSS_type_location
            parts = vehicle_id.split('_')
            if len(parts) >= 2:
                date_part = parts[1]
                formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                
                # Construct URL: http://localhost:8000/static/LOCATION/DATE/plates/VEHICLE_ID_plate.jpg
                plate_url = f"http://localhost:8000/static/{location}/{formatted_date}/plates/{vehicle_id}_plate.jpg"
                return plate_url
            return None
        except Exception as e:
            print(f"Error constructing plate URL for {vehicle_id}: {e}")
            return None

    def parse_color_result(self, result):
        """Parse color result format: 'color_name|#hex_code'"""
        if '|' in result:
            color_name, hex_code = result.split('|', 1)
            return color_name.strip(), hex_code.strip()
        else:
            return result.strip(), "#000000"

    def extract_location_from_vehicle_id(self, vehicle_id):
        """Extract location from vehicle_id format: uuid_timestamp_vehicle_type_LOCATION"""
        try:
            parts = vehicle_id.split('_')
            if len(parts) >= 4:
                location_parts = parts[4:]  # Everything after vehicle type
                return '_'.join(location_parts)
            return "UNKNOWN"
        except:
            return "UNKNOWN"

    def extract_timestamp_from_vehicle_id(self, vehicle_id):
        """Extract timestamp from vehicle_id format: uuid_YYYYMMDD_HHMMSS_vehicle_type_LOCATION"""
        try:
            parts = vehicle_id.split('_')
            if len(parts) >= 3:
                # parts[1] = YYYYMMDD, parts[2] = HHMMSS
                date_part = parts[1]  # YYYYMMDD
                time_part = parts[2]  # HHMMSS
                
                # Parse into datetime components
                year = int(date_part[0:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])
                hour = int(time_part[0:2])
                minute = int(time_part[2:4])
                second = int(time_part[4:6])
                
                # Create datetime object and convert to ISO format
                dt = datetime.datetime(year, month, day, hour, minute, second)
                return dt.isoformat()
            return None
        except Exception as e:
            print(f"Error extracting timestamp from vehicle_id {vehicle_id}: {e}")
            return None

    def save_to_database(self, job_data):
        """Save completed job to database"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO vehicles (vehicle_id, vehicle_type, keyframe_url, plate_url,
                                  color, color_hex, vehicle_number, model, location, timestamp, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            job_data.get("vehicle_id"),
            job_data.get("vehicle_type"),
            job_data.get("keyframe_url"),
            job_data.get("plate_url"),
            job_data.get("color", ""),
            job_data.get("color_hex", "#000000"),
            job_data.get("vehicle_number", ""),
            job_data.get("model", ""),
            job_data.get("location", "UNKNOWN"),
            job_data.get("timestamp"), 
            "completed"
        ))

        conn.commit()
        cursor.close()
        conn.close()
        # Return the data so it can be broadcast
        return job_data
    
    def process_results(self):
        """Main aggregator loop"""
        print("Aggregator started")

        while True:
            try:
                messages = self.r.xreadgroup(
                    AGGREGATOR_GROUP, "aggregator_1",
                    {VEHICLE_RESULTS_STREAM: ">"}, 
                    count=10, block=1000
                )

                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        job_id = fields.get("job_id")
                        worker = fields.get("worker")
                        result = fields.get("result")
                        vehicle_id = fields.get("vehicle_id")

                        print(f"Received result: {job_id} from {worker} -> {result}")

                        if job_id not in self.pending_jobs:
                            location = fields.get("location", self.extract_location_from_vehicle_id(vehicle_id))
                            
                            # extracting from vehicle_id
                            timestamp = self.extract_timestamp_from_vehicle_id(vehicle_id)
                            
                            keyframe_url = self.construct_keyframe_url(vehicle_id, location)
                            plate_url = self.construct_plate_url(vehicle_id, location)
                            self.pending_jobs[job_id] = {
                                "results": {},
                                "vehicle_id": vehicle_id,
                                "location": location,
                                "timestamp": timestamp,
                                "keyframe_url": keyframe_url,
                                "plate_url": plate_url
                            }

                        self.pending_jobs[job_id]["results"][worker] = result
                        vehicle_type = job_id.split("_")[0]
                        expected_workers = get_expected_workers(vehicle_type)

                        received_workers = list(self.pending_jobs[job_id]["results"].keys())
                        if set(received_workers) >= set(expected_workers):
                            print(f"All results received for {job_id}: {received_workers}")

                            results = self.pending_jobs[job_id]["results"]
                            stored_vehicle_id = self.pending_jobs[job_id]["vehicle_id"]
                            location = self.pending_jobs[job_id]["location"]
                            timestamp = self.pending_jobs[job_id]["timestamp"]
                            keyframe_url = self.pending_jobs[job_id]["keyframe_url"]
                            plate_url = self.pending_jobs[job_id]["plate_url"]

                            color_result = results.get("color", "unknown|#000000")
                            color_name, color_hex = self.parse_color_result(color_result)

                            job_data = {
                                "vehicle_id": stored_vehicle_id,
                                "vehicle_type": vehicle_type,
                                "keyframe_url": keyframe_url,
                                "plate_url": plate_url,
                                "color": color_name,
                                "color_hex": color_hex,
                                "vehicle_number": results.get("ocr", ""),
                                "model": results.get("logo", ""),
                                "location": location,
                                "timestamp": timestamp
                            }

                            saved_data = self.save_to_database(job_data)
                            print(f"Saved {job_id} to database: vehicle_id: {stored_vehicle_id}")

                            # broadcast the update
                            # This safely schedules the broadcast on the main event loop.
                            asyncio.run_coroutine_threadsafe(
                                self.manager.broadcast(json.dumps(saved_data, default=str)),
                                self.loop
                            )
                            print(f"Scheduled broadcast for {job_id}")


                            self.r.xadd(VEHICLE_ACK_STREAM, {
                                "job_id": job_id,
                                "status": "completed"
                            })

                            del self.pending_jobs[job_id]

                        self.r.xack(VEHICLE_RESULTS_STREAM, AGGREGATOR_GROUP, msg_id)

            except Exception as e:
                print(f"Aggregator error: {e}")
                time.sleep(1)

# FastAPI Setup
app = FastAPI(title="Sentinel Vehicle API")

# WebSocket Endpoint
@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    # Wait until system is ready before accepting connections
    max_wait = 60  # Maximum 60 seconds wait
    waited = 0
    while not SYSTEM_READY and waited < max_wait:
        await asyncio.sleep(0.5)
        waited += 0.5
    
    if not SYSTEM_READY:
        await websocket.close(code=1008, reason="System not ready")
        print("WebSocket connection rejected: System not ready")
        return
    
    await manager.connect(websocket)
    print("WebSocket client connected successfully")
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("A client disconnected.")

# Endpoint to signal system readiness
@app.post("/internal/system-ready")
async def mark_system_ready():
    """Internal endpoint called by orchestrator when ingress is ready"""
    global SYSTEM_READY
    SYSTEM_READY = True
    print("✓ System marked as READY - WebSocket connections now allowed")
    return {"status": "ready"}

# Endpoint to check system status
@app.get("/api/system/status")
async def get_system_status():
    """Check if system is ready for WebSocket connections"""
    return {
        "ready": SYSTEM_READY,
        "websocket_enabled": SYSTEM_READY
    }

# Database Routes
@app.get("/api/vehicles")
async def get_vehicles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vehicle_id, vehicle_type, keyframe_url, plate_url, color, color_hex, vehicle_number, model, location, timestamp
        FROM vehicles 
        ORDER BY timestamp DESC 
        LIMIT 100
    """)
    vehicles = [
        {
            "vehicle_id": row[0],
            "vehicle_type": row[1],
            "keyframe_url": row[2],
            "plate_url": row[3],
            "color": row[4],
            "color_hex": row[5],
            "vehicle_number": row[6],
            "model": row[7],
            "location": row[8],
            "timestamp": row[9],
        }
        for row in cursor.fetchall()
    ]
    cursor.close()
    conn.close()
    return vehicles


@app.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    cursor.close()
    conn.close()

    return {
        "id": row[0],
        "vehicle_id": row[1],
        "vehicle_type": row[2],
        "keyframe_url": row[3],
        "plate_url": row[4],
        "color": row[5],
        "color_hex": row[6],
        "vehicle_number": row[7],
        "model": row[8],
        "location": row[9],
        "timestamp": row[10],
        "status": row[11]
    }


# File Browser Integration
BASE_DIR = Path(__file__).resolve().parent
WEB_ROOT = BASE_DIR / "web"
STATIC_PATH = WEB_ROOT / "static"
TEMPLATES_PATH = WEB_ROOT / "templates"

# Make sure directories exist
WEB_ROOT.mkdir(exist_ok=True)
STATIC_PATH.mkdir(exist_ok=True)
LOCATION_PATH = STATIC_PATH / LOCATION
LOCATION_PATH.mkdir(parents=True, exist_ok=True)
TEMPLATES_PATH.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_PATH))


@app.get("/", response_class=HTMLResponse)
async def file_browser(request: Request, subpath: str = ""):
    """Browse local static files with breadcrumbs."""
    full_path = STATIC_PATH / subpath
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    # Serve file directly
    if full_path.is_file():
        return FileResponse(full_path)

    # Build folder + file listings
    items = os.listdir(full_path)
    folders, files = [], []

    for name in sorted(items, key=lambda a: a.lower()):
        p = full_path / name
        mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        if p.is_dir():
            folders.append({
                "name": name,
                "href": f"/?subpath={subpath + '/' + name if subpath else name}",
                "mtime": mtime
            })
        else:
            size = p.stat().st_size
            size_str = (
                f"{size} B" if size < 1024
                else f"{size/1024:.1f} KB" if size < 1024 * 1024
                else f"{size/(1024*1024):.1f} MB"
            )
            files.append({
                "name": name,
                "href": f"/static/{subpath + '/' + name if subpath else name}",
                "size_str": size_str,
                "mtime": mtime,
                "is_image": name.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
            })

    # Breadcrumbs
    parts = subpath.strip("/").split("/") if subpath else []
    breadcrumbs = [{"name": "Root", "href": "/"}]
    current = ""
    for part in parts:
        current += "/" + part
        breadcrumbs.append({"name": part, "href": f"/?subpath={current.strip('/')}"})


    parent_dir = None
    if subpath:
        parent_dir = f"/?subpath={'/'.join(parts[:-1])}" if len(parts) > 1 else "/"

    return templates.TemplateResponse("file_browser.html", {
        "request": request,
        "relative_path": subpath or "/",
        "folders": folders,
        "files": files,
        "breadcrumbs": breadcrumbs,
        "parent_dir": parent_dir,
        "location": LOCATION,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.get("/stream_feed")
async def stream_feed():
    """MJPEG streaming endpoint for RTSP feed."""
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/stream", response_class=HTMLResponse)
async def stream_page(request: Request):
    """Render a live stream viewer page."""
    return templates.TemplateResponse("stream.html", {"request": request, "location": LOCATION})

# Added this event route to asynchronous loop in the baground to run web socket requests 
@app.on_event("startup")
async def startup_event():
    # Get the current asyncio event loop
    loop = asyncio.get_running_loop()
    
    # Instantiate the aggregator, passing it the manager and the loop
    aggregator = ResultAggregator(manager, loop)
    
    # Start the process_results function loop in its own thread , does not interfere with the web server 
    aggregator_thread = threading.Thread(target=aggregator.process_results, daemon=True)
    aggregator_thread.start()
    
    print("Aggregator background thread has been scheduled.")

# Entrypoint 
if __name__ == "__main__":
    import uvicorn
    print("Starting Sentinel Aggregator Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

