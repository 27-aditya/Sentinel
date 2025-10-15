import cv2
import os
import numpy as np
import uuid
import datetime
from pathlib import Path
from ultralytics import YOLO
from db_redis.sentinel_redis_config import *
import pytz

IST = pytz.timezone('Asia/Kolkata')

model = YOLO("yolov8s.pt")
plate_model = YOLO("license_plate_detector.pt")

# Get configuration from environment
LOCATION = os.getenv("LOCATION", "DEFAULT_LOCATION")
rtsp_url = os.getenv("RTSP_STREAM")

print(f"Ingress started for location: {LOCATION}")

if not rtsp_url:
    print("Error: RTSP_STREAM not set in environment variables.")
    exit(1)

# Initialize video capture
cap = cv2.VideoCapture(rtsp_url)
if not cap.isOpened():
    print(f"Error: Cannot connect to RTSP stream at {rtsp_url}")
    exit(1)

# Set up storage paths - store directly in web/static structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent 
AGGREGATOR_WEB_ROOT = PROJECT_ROOT / "aggregator" / "web"
STATIC_PATH = AGGREGATOR_WEB_ROOT / "static"
LOCATION_PATH = STATIC_PATH / LOCATION

def ensure_storage_structure():
    """Ensure the aggregator/web/static/location directory structure exists"""
    AGGREGATOR_WEB_ROOT.mkdir(exist_ok=True)
    STATIC_PATH.mkdir(exist_ok=True)
    LOCATION_PATH.mkdir(exist_ok=True)
    print(f"Storage structure initialized: {LOCATION_PATH}")

def get_date_folder():
    """Get or create today's date folder with keyframes and plates subdirectories"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    date_folder = LOCATION_PATH / today
    keyframes_folder = date_folder / "keyframes"
    plates_folder = date_folder / "plates"
    
    # Create all directories
    keyframes_folder.mkdir(parents=True, exist_ok=True)
    plates_folder.mkdir(parents=True, exist_ok=True)
    
    return date_folder, today

def save_keyframe_organized(vehicle_crop, vehicle_id):
    """Save keyframe in organized structure: /aggregator/web/static/LOCATION/DATE/keyframes/VEHICLE_ID.jpg"""
    try:
        date_folder, date_str = get_date_folder()
        keyframes_folder = date_folder / "keyframes"
        filename = f"{vehicle_id}.jpg"
        file_path = keyframes_folder / filename
        
        # Save the image
        success = cv2.imwrite(str(file_path), vehicle_crop)
        
        if success:
            relative_path = f"static/{LOCATION}/{date_str}/keyframes/{filename}"
            print(f"Saved keyframe: {relative_path}")
            print(f"Full path: {file_path}")
            return str(file_path), relative_path
        else:
            print(f"Failed to save keyframe for {vehicle_id}")
            return None, None
            
    except Exception as e:
        print(f"Error saving keyframe for {vehicle_id}: {e}")
        return None, None


def detect_and_save_plate(vehicle_crop, vehicle_id):
    """Detect license plate in vehicle crop and save it in plates subdirectory"""
    
    # If plate model is not loaded, return None, None
    if plate_model is None:
        return None, None
    
    try:
        results = plate_model(vehicle_crop, verbose=False)
        
        if len(results) > 0 and len(results[0].boxes) > 0:
            # Get the first detected plate
            box = results[0].boxes[0]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Crop plate from vehicle image
            plate_crop = vehicle_crop[y1:y2, x1:x2]
            
            # Save plate image in plates subdirectory
            plate_filename = f"{vehicle_id}_plate.jpg"
            
            # Get organized path for the vehicle (reuse existing date folder)
            date_folder, date_str = get_date_folder()
            plates_folder = date_folder / "plates"
            
            plate_path = plates_folder / plate_filename
            cv2.imwrite(str(plate_path), plate_crop)
            
            # Construct relative path for URL
            plate_relative_path = f"static/{LOCATION}/{date_str}/plates/{plate_filename}"
            
            print(f"  - Saved plate: {plate_relative_path}")
            return str(plate_path), plate_relative_path
        else:
            # No plate detected, return a tuple of Nones
            return None, None
            
    except Exception as e:
        print(f"Error during plate detection for {vehicle_id}: {e}")
        # On error, return a tuple of Nones
        return None, None


# Initialize storage structure
ensure_storage_structure()

# Connect to Redis
r = get_redis_connection()

# Track saved vehicles to avoid duplicates
saved_ids = set()

# Set up video capture
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
FRAME_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
FRAME_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Connected to RTSP stream: {FRAME_WIDTH}x{FRAME_HEIGHT}")

# Define keyframe trigger zone
ZONE_X1 = 0
ZONE_Y1 = 200
ZONE_X2 = 1500
ZONE_Y2 = 800
TRIGGER_ZONE = (ZONE_X1, ZONE_Y1, ZONE_X2, ZONE_Y2)

def publish_job(vehicle_type, organized_path, relative_path, track_id, vehicle_id, plate_path=None, plate_relative_path=None):
    """Publish job with organized file paths"""
    timestamp = datetime.datetime.now(IST)
    job_id = f"{vehicle_type}_{track_id}_{vehicle_id.split('_')[0]}"  
    
    payload = {
        "job_id": job_id,
        "vehicle_id": vehicle_id, 
        "vehicle_type": vehicle_type,
        "frame_path": organized_path,   
        "plate_path": plate_path if plate_path else "None",   
        "frame_url": relative_path,  
        "plate_url": plate_relative_path if plate_relative_path else "None",
        "timestamp": timestamp.isoformat(),
        "location": LOCATION
    }
    
    r.xadd(VEHICLE_JOBS_STREAM, payload)
    print(f"Published job: {job_id} (Vehicle ID: {vehicle_id}) @ {LOCATION}")
    print(f"  Keyframe stored: {relative_path}")

# Main processing loop
frame_num = 0
print("Starting vehicle detection...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from RTSP stream")
        cap.release()
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        continue
        
    frame_num += 1
    tz_x1, tz_y1, tz_x2, tz_y2 = TRIGGER_ZONE

    # Run YOLO tracking
    results = model.track(frame, classes=[2, 3, 5, 7], verbose=False, tracker="bytetrack.yaml", persist=True)

    if results[0].boxes is not None and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        track_ids = results[0].boxes.id.int().cpu().numpy()
        class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            track_id = track_ids[i]
            class_id = class_ids[i]

            # Apply motorcycle padding
            if class_id == 3:  # motorcycle
                box_height = y2 - y1
                padding_top = int(box_height * 2.5)
                padding_sides = int((x2 - x1) * 0.2)
                y1_padded = max(0, y1 - padding_top)
                x1_padded = max(0, x1 - padding_sides)
                x2_padded = min(FRAME_WIDTH, x2 + padding_sides)
                y2_padded = y2
            else:
                y1_padded, x1_padded, x2_padded, y2_padded = y1, x1, x2, y2

            # Check if vehicle is in trigger zone
            vehicle_center_x = (x1 + x2) // 2
            vehicle_bottom_y = y2

            if (tz_x1 < vehicle_center_x < tz_x2) and (tz_y1 < vehicle_bottom_y < tz_y2):
                if track_id not in saved_ids:
                    saved_ids.add(track_id)

                    vehicle_type = model.names[class_id]
                    
                    # Generate vehicle ID with timestamp, type, and location
                    timestamp = datetime.datetime.now(IST)
                    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
                    uuid_part = uuid.uuid4().hex[:8]
                    vehicle_id = f"{uuid_part}_{timestamp_str}_{vehicle_type}_{LOCATION}"
                    
                    print(f"Vehicle '{vehicle_type}' ID {track_id} detected -> {vehicle_id}")

                    # Extract and save vehicle crop
                    vehicle_crop = frame[y1_padded:y2_padded, x1_padded:x2_padded]
                    if vehicle_crop.size > 0:
                        # Save in organized structure
                        organized_path, relative_path = save_keyframe_organized(vehicle_crop, vehicle_id)
                        
                        if organized_path and relative_path:
                            # Detect and save plate if model is availabl
                            plate_path, plate_relative_path = detect_and_save_plate(vehicle_crop, vehicle_id)
                            publish_job(vehicle_type, organized_path, relative_path, track_id, vehicle_id, plate_path, plate_relative_path)
                        else:
                            print(f"Failed to save keyframe for {vehicle_id}")

cap.release()
cv2.destroyAllWindows()
print("Ingress stopped")
