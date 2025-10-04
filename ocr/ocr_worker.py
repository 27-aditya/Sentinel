import time
import random
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'db_redis'))
from sentinel_redis_config import *

def process_ocr(frame_path, plate_path):
    """Dummy OCR processing - replace with real OCR"""
    # Simulate processing time
    time.sleep(random.uniform(0.5, 2.0))
    
    # Return dummy license plate
    dummy_plates = ["ABC123", "XYZ789", "DEF456", "GHI012", "JKL345"]
    return random.choice(dummy_plates)

def ocr_worker():
    r = get_redis_connection()
    worker_id = "ocr_worker_1"
    
    print(f"OCR Worker started: {worker_id}")
    
    while True:
        try:
            # Read from OCR group
            messages = r.xreadgroup(
                OCR_GROUP, worker_id, 
                {VEHICLE_JOBS_STREAM: ">"}, 
                count=1, block=BLOCK_TIME
            )
            
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    job_id = fields.get("job_id")
                    vehicle_type = fields.get("vehicle_type")
                    frame_path = fields.get("frame_path")
                    plate_path = fields.get("plate_path")
                    
                    print(f"OCR processing job: {job_id} ({vehicle_type})")
                    
                    # Process OCR for all vehicle types
                    if should_worker_process("ocr", vehicle_type):
                        try:
                            result = process_ocr(frame_path, plate_path)
                            
                            # Publish result
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "worker": "ocr",
                                "result": result,
                                "status": "ok"
                            })
                            
                            print(f"OCR completed: {job_id} -> {result}")
                            
                            # Acknowledge message
                            r.xack(VEHICLE_JOBS_STREAM, OCR_GROUP, msg_id)
                            
                        except Exception as e:
                            print(f"OCR failed for {job_id}: {e}")
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "worker": "ocr",
                                "result": "",
                                "status": "error",
                                "error": str(e)
                            })
                    else:
                        print(f"OCR skipping {vehicle_type} (not in scope)")
                        r.xack(VEHICLE_JOBS_STREAM, OCR_GROUP, msg_id)
                        
        except Exception as e:
            print(f"OCR worker error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    ocr_worker()
