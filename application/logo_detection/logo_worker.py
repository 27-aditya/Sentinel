import time
import random
import signal
import sys
import threading
from db_redis.sentinel_redis_config import *

shutdown_event = threading.Event()

def handle_shutdown(signum, frame):
    print(f"\nReceived signal {signum}, shutting down Logo worker gracefully...")
    shutdown_event.set()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def process_logo(frame_path):
    """Dummy logo/model detection - replace with real model inference."""
    time.sleep(random.uniform(1.0, 3.0))
    models = ["Honda", "Toyota", "BMW", "Mercedes"]
    return random.choice(models)

def logo_worker():
    r = get_redis_connection()
    worker_id = "logo_worker_1"
    
    print(f"[Logo] Worker started: {worker_id}")
    
    while not shutdown_event.is_set():
        try:
            messages = r.xreadgroup(
                LOGO_GROUP, worker_id,
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
                    
                    print(f"[Logo] Processing job: {job_id} ({vehicle_type})")
                    
                    if should_worker_process("logo", vehicle_type):
                        try:
                            result = process_logo(frame_path)
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "vehicle_id": fields.get("vehicle_id"),
                                "worker": "logo",
                                "result": result,
                                "status": "ok"
                            })
                            print(f"[Logo] Completed: {job_id} -> {result}")
                            r.xack(VEHICLE_JOBS_STREAM, LOGO_GROUP, msg_id)
                        except Exception as e:
                            print(f"[Logo] Failed for {job_id}: {e}")
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "worker": "logo",
                                "result": "",
                                "status": "error",
                                "error": str(e)
                            })
                    else:
                        print(f"[Logo] Skipping {vehicle_type} (not in scope)")
                        r.xack(VEHICLE_JOBS_STREAM, LOGO_GROUP, msg_id)
                        
        except Exception as e:
            print(f"[Logo] Worker error: {e}")
            time.sleep(1)
    
    print("[Logo] Shutdown complete.")

if __name__ == "__main__":
    logo_worker()
