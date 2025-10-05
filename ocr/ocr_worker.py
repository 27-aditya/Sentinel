import time
import random
import signal
import sys
import threading
from db_redis.sentinel_redis_config import *

shutdown_event = threading.Event()

def handle_shutdown(signum, frame):
    print(f"\nReceived signal {signum}, shutting down OCR worker gracefully...")
    shutdown_event.set()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def process_ocr(frame_path, plate_path):
    """Dummy OCR processing - replace with actual OCR model."""
    time.sleep(random.uniform(0.5, 2.0))
    dummy_plates = ["ABC123", "XYZ789", "DEF456", "GHI012", "JKL345"]
    return random.choice(dummy_plates)

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
