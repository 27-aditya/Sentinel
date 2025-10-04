import time
import random
from db_redis.sentinel_redis_config import *

def process_color(frame_path):
    """Dummy color detection - replace with real color detection"""
    time.sleep(random.uniform(0.3, 1.5))
    
    colors = ["red", "blue", "white", "black", "silver", "green", "yellow"]
    return random.choice(colors)

def color_worker():
    r = get_redis_connection()
    worker_id = "color_worker_1"
    
    print(f"Color Worker started: {worker_id}")
    
    while True:
        try:
            messages = r.xreadgroup(
                COLOR_GROUP, worker_id,
                {VEHICLE_JOBS_STREAM: ">"}, 
                count=1, block=BLOCK_TIME
            )
            
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    job_id = fields.get("job_id")
                    vehicle_type = fields.get("vehicle_type")
                    frame_path = fields.get("frame_path")
                    
                    print(f"Color processing job: {job_id} ({vehicle_type})")
                    
                    # Only process cars
                    if should_worker_process("color", vehicle_type):
                        try:
                            result = process_color(frame_path)
                            
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "worker": "color",
                                "result": result,
                                "status": "ok"
                            })
                            
                            print(f"Color completed: {job_id} -> {result}")
                            r.xack(VEHICLE_JOBS_STREAM, COLOR_GROUP, msg_id)
                            
                        except Exception as e:
                            print(f"Color failed for {job_id}: {e}")
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "worker": "color", 
                                "result": "",
                                "status": "error",
                                "error": str(e)
                            })
                    else:
                        print(f"Color skipping {vehicle_type} (cars only)")
                        r.xack(VEHICLE_JOBS_STREAM, COLOR_GROUP, msg_id)
                        
        except Exception as e:
            print(f"Color worker error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    color_worker()
