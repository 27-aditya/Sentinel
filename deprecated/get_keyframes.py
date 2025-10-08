# import cv2
# import os
# import numpy as np
# from ultralytics import YOLO

# # YOLO models are initialized here , we can swap out with custom models as well but YOLO works really well for detection 
# model = YOLO("yolov8s.pt")

# # The output directory for saving keyframes
# os.makedirs("keyframes", exist_ok=True)

# # Track saved vehicles to avoid duplicates after the object tracker has given them IDs
# saved_ids = set()

# # Open video or stream
# cap = cv2.VideoCapture("../video.mp4")

# # We need the frame dimensions for defining the trigger zone
# FRAME_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# FRAME_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# # Define the Keyframe Trigger Zone ( its a region where if a vehicle enters it, we save a keyframe )
# # Measured in pixels 
# CENTER_LINE_Y = 500 
# ZONE_EXPANSION = 250
# TRIGGER_ZONE = (0, CENTER_LINE_Y - ZONE_EXPANSION, FRAME_WIDTH, CENTER_LINE_Y + ZONE_EXPANSION)

# frame_num = 0
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#     frame_num += 1

#     # ------- We can use this for reference to draw the trigger zone on the frame - useful for debugging but comment id out for now since the box might interfere with number plate OCR ------
    
#     # # Draw the Trigger Zone
#     tz_x1, tz_y1, tz_x2, tz_y2 = TRIGGER_ZONE
#     # cv2.rectangle(frame, (tz_x1, tz_y1), (tz_x2, tz_y2), (0, 255, 255), 2)
#     # cv2.putText(frame, "Trigger Zone", (tz_x1 + 10, tz_y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

#     # part of the ultralytics package, it does detection and tracking in one go
#     results = model.track(
#         frame,
#         classes=[2, 3, 5, 7],
#         verbose=False,
#         tracker="bytetrack.yaml",
#         persist=True
#     )
    
#     # if there is a detection in the frame , and if the object tracker has assigned an ID to it 
#     if results[0].boxes is not None and results[0].boxes.id is not None:
#         boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
#         track_ids = results[0].boxes.id.int().cpu().numpy()
#         class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

#         for i, box in enumerate(boxes):
#             x1, y1, x2, y2 = box
#             track_id = track_ids[i]
#             class_id = class_ids[i]

#             # This part is for 2 wheeler padding , we want to capture more of the bike and rider in the crop , YOLO box is usually tight around the plate 
#             if class_id == 3:
#                 box_height = y2 - y1
                
#                 # Increased padding for more height 
#                 padding_top = int(box_height * 2.5) # 250% to top
                
#                 padding_sides = int((x2 - x1) * 0.2) # 20% to sides
                
#                 # Apply padding with boundary checks
#                 y1_padded = max(0, y1 - padding_top)
#                 x1_padded = max(0, x1 - padding_sides)
#                 x2_padded = min(FRAME_WIDTH, x2 + padding_sides)
#                 y2_padded = y2 # Bottom stays the same
#             else:
#                 # For cars, use the original box
#                 y1_padded, x1_padded, x2_padded, y2_padded = y1, x1, x2, y2
            
#             #  Commenting drawing the bounding box out for now since the box might interfere with number plate OCR
            
#             # Draw bounding box and ID on the frame
#             # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#             # cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#             # Check trigger zone using original box's bottom-center
#             vehicle_center_x = (x1 + x2) // 2
#             vehicle_bottom_y = y2

#             # checking if the frame of the vehile we got is within the trigger zone
#             if (tz_x1 < vehicle_center_x < tz_x2) and (tz_y1 < vehicle_bottom_y < tz_y2):
#                 if track_id not in saved_ids:
#                     saved_ids.add(track_id)
                    
#                     vehicle_type = model.names[class_id]
#                     print(f"Vehicle of class '{vehicle_type}' assigned ID {track_id}")

#                     # Crop using the PADDED coordinates
#                     vehicle_crop = frame[y1_padded:y2_padded, x1_padded:x2_padded]
                    
#                     if vehicle_crop.size > 0:
#                         vehicle_type = model.names[class_id]
#                         filename = f"keyframes/{vehicle_type}_{track_id}_frame{frame_num}.jpg"
                        
#                         # ____________________________ # 
#                         # Heres where we save the keyframe to the output directory
#                         # ____________________________ #
#                         cv2.imwrite(filename, vehicle_crop)
#                         print(f"Vehicle ID {track_id} triggered. Saved keyframe: {filename}")
#                         cv2.circle(frame, (vehicle_center_x, vehicle_bottom_y), 5, (0, 0, 255), -1)

#     # The pre view window 
#     cv2.imshow("Vehicle Trigger System", frame)
    
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# if hasattr(cv2, "destroyAllWindows"):
#     try:
#         cv2.destroyAllWindows()
#     except:
#         pass

import cv2
import os
import numpy as np
from ultralytics import YOLO

# YOLO models are initialized here
model = YOLO("yolov8s.pt")

# The output directory for saving keyframes
os.makedirs("keyframes", exist_ok=True)

# --- NEW: Counters for performance monitoring ---
# Track all unique IDs ever seen by the tracker
seen_ids = set()
# Count the number of frames actually saved
frames_saved_count = 0

# Track saved vehicles to avoid duplicates
saved_ids = set()

# Open video or stream
cap = cv2.VideoCapture("../video.mp4")

# We need the frame dimensions for boundary checks
FRAME_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
FRAME_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Define a more precise, rectangular Trigger Zone (x1, y1, x2, y2)
# --- TUNE THESE VALUES FOR YOUR VIDEO ---
ZONE_X1 = 0
ZONE_Y1 = 200
ZONE_X2 = 1500
ZONE_Y2 = 800
# ---
TRIGGER_ZONE = (ZONE_X1, ZONE_Y1, ZONE_X2, ZONE_Y2)

frame_num = 0 
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_num += 1

    # --- NEW: Highlight the trigger zone with a semi-transparent overlay ---
    # Time and space complexity: O(W*H) for the copy and blend, where W and H are frame dimensions.
    overlay = frame.copy()
    tz_x1, tz_y1, tz_x2, tz_y2 = TRIGGER_ZONE
    # Draw a filled, semi-transparent rectangle on the overlay
    cv2.rectangle(overlay, (tz_x1, tz_y1), (tz_x2, tz_y2), (0, 255, 255), -1) # Yellow, filled
    alpha = 0.3  # Transparency factor
    # Blend the overlay with the original frame
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
    # Draw a solid border on top for clarity
    cv2.rectangle(frame, (tz_x1, tz_y1), (tz_x2, tz_y2), (0, 255, 255), 2)


    # Detection and tracking
    results = model.track(
        frame,
        classes=[2, 3, 5, 7],
        verbose=False,
        tracker="bytetrack.yaml",
        persist=True
    )

    if results[0].boxes is not None and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        track_ids = results[0].boxes.id.int().cpu().numpy()
        class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            track_id = track_ids[i]
            class_id = class_ids[i]
            
            # --- NEW: Add every seen ID to our monitoring set ---
            # Time and space complexity: O(1) on average for set insertion.
            seen_ids.add(track_id)

            # Padding for two-wheelers
            if class_id == 3:
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

            # Check if the vehicle is inside the trigger zone
            if (tz_x1 < vehicle_center_x < tz_x2) and (tz_y1 < vehicle_bottom_y < tz_y2):
                if track_id not in saved_ids:
                    saved_ids.add(track_id)
                    
                    vehicle_type = model.names[class_id]
                    print(f"Vehicle of class '{vehicle_type}' with ID {track_id} entered the trigger zone.")

                    vehicle_crop = frame[y1_padded:y2_padded, x1_padded:x2_padded]
                    
                    if vehicle_crop.size > 0:
                        filename = f"keyframes/{vehicle_type}_{track_id}_frame{frame_num}.jpg"
                        cv2.imwrite(filename, vehicle_crop)
                        print(f"Saved keyframe: {filename}")
                        
                        # --- NEW: Increment the saved frames counter ---
                        frames_saved_count += 1
                        
                        cv2.circle(frame, (vehicle_center_x, vehicle_bottom_y), 5, (0, 0, 255), -1)

    # --- NEW: Display the real-time stats on the frame ---
    stats_text_seen = f"Seen IDs: {len(seen_ids)}"
    stats_text_saved = f"Saved Frames: {frames_saved_count}"
    cv2.putText(frame, stats_text_seen, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
    cv2.putText(frame, stats_text_seen, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, stats_text_saved, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
    cv2.putText(frame, stats_text_saved, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # The preview window
    cv2.imshow("Vehicle Trigger System", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if hasattr(cv2, "destroyAllWindows"):
    try:
        cv2.destroyAllWindows()
    except:
        pass

# --- NEW: Print a final summary on exit ---
print("\n--- FINAL SUMMARY ---")
print(f"Total unique vehicle IDs seen: {len(seen_ids)}")
print(f"Total keyframes saved: {frames_saved_count}")
if len(seen_ids) > 0:
    capture_rate = (frames_saved_count / len(seen_ids)) * 100
    print(f"Capture Rate: {capture_rate:.2f}%")
print("---------------------\n")

