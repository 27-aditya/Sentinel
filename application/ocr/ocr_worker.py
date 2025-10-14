import re
import time
import signal
import threading
from rapidocr_onnxruntime import RapidOCR
import numpy as np
import cv2

from db_redis.sentinel_redis_config import *

shutdown_event = threading.Event()

def handle_shutdown(signum, frame):
    print(f"\nReceived signal {signum}, shutting down OCR worker gracefully...")
    shutdown_event.set()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# Replaced EasyOCR with RapidOCR
reader = RapidOCR()
print("RapidOCR reader initialized.")


def process_ocr(frame_path, plate_path):
    """Actual OCR model, now using RapidOCR without formatting"""

    if not plate_path or not os.path.exists(plate_path):
        print(f"OCR Error: Plate path '{plate_path}' is invalid or does not exist.")
        return None

    try:
        plate_image = cv2.imread(plate_path)

        # actual line of code commented out 
        
        if plate_image is None:
            print(f"OCR Error: Failed to read image from {plate_path}. Returning N/A.")
            return "N/A"

        # --- Tuned Parameters ---
        scale_factor = 3.0

        # --- Image Processing Pipeline ---
        gray_image = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)

        # Resize image 
        width = int(gray_image.shape[1] * scale_factor)
        height = int(gray_image.shape[0] * scale_factor)
        resized_image = cv2.resize(gray_image, (width, height), interpolation=cv2.INTER_CUBIC)

        # Sharpening filter
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened_image = cv2.filter2D(resized_image, -1, kernel)

        # RapidOCR returns (result, elapse)
        results, _ = reader(sharpened_image)

        if not results:
            print("OCR Info: RapidOCR found no text.")
            return "N/A"

        # Extract text from RapidOCR result tuples
        raw_text = "".join([res[1] for res in results])
        cleaned_text = re.sub(r'[^A-Z0-9]', '', raw_text).strip()

        # Check length only (no formatting)
        if 0 < len(cleaned_text) <= 10:
            print(f"OCR Success: Found plate '{cleaned_text}' from {os.path.basename(plate_path)}")
            return cleaned_text
        else:
            print(f"OCR Validation Failed: Raw text '{cleaned_text}' failed length check. Returning N/A.")
            return "N/A"

    except Exception as e:
        print(f"An unexpected error occurred during OCR process for {plate_path}: {e}")
        return "N/A"


def ocr_worker():
    r = get_redis_connection()
    worker_id = "ocr_worker_1"
    
    print(f"[OCR] Worker started: {worker_id}")
    
    while not shutdown_event.is_set():
        try:
            messages = r.xreadgroup(
                OCR_GROUP, worker_id, 
                {VEHICLE_JOBS_STREAM: ">"}, 
                count=1, block=BLOCK_TIME
            )
            
            if not messages:
                continue
            
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    job_id = fields.get("job_id")
                    vehicle_type = fields.get("vehicle_type")
                    frame_path = fields.get("frame_path")
                    plate_path = fields.get("plate_path")
                    
                    print(f"[OCR] Processing job: {job_id} ({vehicle_type})")
                    
                    if should_worker_process("ocr", vehicle_type):
                        try:
                            result = process_ocr(frame_path, plate_path)
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "vehicle_id": fields.get("vehicle_id"),
                                "worker": "ocr",
                                "result": result,
                                "status": "ok"
                            })
                            print(f"[OCR] Completed: {job_id} -> {result}")
                            r.xack(VEHICLE_JOBS_STREAM, OCR_GROUP, msg_id)
                        except Exception as e:
                            print(f"[OCR] Failed for {job_id}: {e}")
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "worker": "ocr",
                                "result": "",
                                "status": "error",
                                "error": str(e)
                            })
                    else:
                        print(f"[OCR] Skipping {vehicle_type} (not in scope)")
                        r.xack(VEHICLE_JOBS_STREAM, OCR_GROUP, msg_id)
                        
        except Exception as e:
            print(f"[OCR] Worker error: {e}")
            time.sleep(1)
    
    print("[OCR] Shutdown complete.")

if __name__ == "__main__":
    ocr_worker()