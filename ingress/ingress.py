import cv2
import os
import numpy as np
import uuid
import datetime
from ultralytics import YOLO
from db_redis.sentinel_redis_config import *

# ---------------- CONFIG ----------------
model = YOLO("yolov8s.pt")

# Get the LOCATION from the orchestrator
LOCATION = os.getenv("LOCATION", "DEFAULT_LOCATION")
print(f"Ingress started for location: {LOCATION}")

# The output directory for saving keyframes
os.makedirs("keyframes", exist_ok=True)
os.makedirs("processed_keyframes", exist_ok=True)

# Connect Redis using config
r = get_redis_connection()

# Track saved vehicles to avoid duplicates
saved_ids = set()

# RTSP connection
cap = cv2.VideoCapture("rtsp://127.0.0.1:8554/stream")
if not cap.isOpened():
    print("Error: Cannot connect to RTSP stream")
    exit()

cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
FRAME_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
FRAME_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Connected to RTSP stream: {FRAME_WIDTH}x{FRAME_HEIGHT}")

# Define keyframe trigger zone
CENTER_LINE_Y = 500
ZONE_EXPANSION = 250
TRIGGER_ZONE = (0, CENTER_LINE_Y - ZONE_EXPANSION, FRAME_WIDTH, CENTER_LINE_Y + ZONE_EXPANSION)

def preprocess_for_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.medianBlur(gray, 5)
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return binary

def publish_job(vehicle_type, frame_path, plate_path, track_id):
    timestamp = datetime.datetime.utcnow()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    
    uuid_part = uuid.uuid4().hex[:8]
    vehicle_id = f"{uuid_part}_{timestamp_str}_{vehicle_type}_{LOCATION}"
    
    job_id = f"{vehicle_type}_{track_id}_{uuid_part}"
    
    payload = {
        "job_id": job_id,
        "vehicle_id": vehicle_id, 
        "vehicle_type": vehicle_type,
        "frame_path": frame_path,
        "plate_path": plate_path,
        "timestamp": timestamp.isoformat(),
        "location": LOCATION
    }
    r.xadd(VEHICLE_JOBS_STREAM, payload)
    print(f"Published job: {job_id} (Vehicle ID: {vehicle_id}) @ {LOCATION}")

# Main loop
frame_num = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from RTSP stream")
        cap.release()
        cap = cv2.VideoCapture("rtsp://127.0.0.1:8554/stream")
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        continue
        
    frame_num += 1
    tz_x1, tz_y1, tz_x2, tz_y2 = TRIGGER_ZONE

    results = model.track(frame, classes=[2, 3, 5, 7], verbose=False, tracker="bytetrack.yaml", persist=True)

    if results[0].boxes is not None and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        track_ids = results[0].boxes.id.int().cpu().numpy()
        class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            track_id = track_ids[i]
            class_id = class_ids[i]

            if class_id == 3:  # motorcycle padding
                box_height = y2 - y1
                padding_top = int(box_height * 2.5)
                padding_sides = int((x2 - x1) * 0.2)
                y1_padded = max(0, y1 - padding_top)
                x1_padded = max(0, x1 - padding_sides)
                x2_padded = min(FRAME_WIDTH, x2 + padding_sides)
                y2_padded = y2
            else:
                y1_padded, x1_padded, x2_padded, y2_padded = y1, x1, x2, y2

            vehicle_center_x = (x1 + x2) // 2
            vehicle_bottom_y = y2

            if (tz_x1 < vehicle_center_x < tz_x2) and (tz_y1 < vehicle_bottom_y < tz_y2):
                if track_id not in saved_ids:
                    saved_ids.add(track_id)

                    vehicle_type = model.names[class_id]
                    print(f"Vehicle of class '{vehicle_type}' assigned ID {track_id}")

                    vehicle_crop = frame[y1_padded:y2_padded, x1_padded:x2_padded]
                    if vehicle_crop.size > 0:
                        filename = f"keyframes/{vehicle_type}_{track_id}_frame{frame_num}.jpg"
                        cv2.imwrite(filename, vehicle_crop)

                        processed = preprocess_for_ocr(vehicle_crop)
                        plate_filename = f"processed_keyframes/{vehicle_type}_{track_id}_frame{frame_num}_plate.jpg"
                        cv2.imwrite(plate_filename, processed)

                        publish_job(vehicle_type, filename, plate_filename, track_id)

    cv2.imshow("Vehicle Trigger System", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
