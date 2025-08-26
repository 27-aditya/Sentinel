import cv2
import os
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# Load YOLOv8 model (make sure you have yolov8n.pt or yolov8s.pt downloaded)
model = YOLO("yolov8n.pt")

# Initialize DeepSORT tracker
tracker = DeepSort(max_age=30)

# Create output directory
os.makedirs("keyframes", exist_ok=True)

# Track saved vehicles to avoid duplicates
saved_ids = set()

# Open video or stream
cap = cv2.VideoCapture("/mnt/c/Stuff/CCTV Footage/KAKKODI_MUKKU_JN_ch7_20250811100000_20250811103017.mp4")   # Replace with 0 for webcam, or RTSP/HTTP stream

frame_num = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_num += 1

    # Run YOLO detection (only vehicles: car=2, motorcycle=3, bus=5, truck=7 in COCO dataset)
    results = model(frame, classes=[2, 3, 5, 7], verbose=False)
    detections = results[0].boxes.xyxy.cpu().numpy()  # [x1,y1,x2,y2,conf,class]
    confidences = results[0].boxes.conf.cpu().numpy()
    class_ids = results[0].boxes.cls.cpu().numpy()

    dets_for_tracker = []
    for det, conf, cls_id in zip(detections, confidences, class_ids):
        x1, y1, x2, y2 = det[:4]
        dets_for_tracker.append(([x1, y1, x2 - x1, y2 - y1], conf, str(int(cls_id))))

    # Update tracker
    tracks = tracker.update_tracks(dets_for_tracker, frame=frame)

    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id

        # Save one keyframe per vehicle ID
        if track_id not in saved_ids:
            saved_ids.add(track_id)
            filename = f"keyframes/vehicle_{track_id}_frame{frame_num}.jpg"
            cv2.imwrite(filename, frame)
            print(f"[INFO] Saved keyframe: {filename}")

cap.release()
print("✅ Done. Keyframes saved in 'keyframes/' folder.")