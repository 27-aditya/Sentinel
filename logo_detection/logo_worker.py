import time
import random
from db_redis.sentinel_redis_config import *

def process_logo(frame_path):
    """Dummy logo/model detection - replace with real logo detection"""
    time.sleep(random.uniform(1.0, 3.0))
    
    models = ["Honda", "Toyota", "BMW", "Mercedes"]
    return random.choice(models)

def logo_worker():
    r = get_redis_connection()
    worker_id = "logo_worker_1"
    
    print(f"Logo Worker started: {worker_id}")
    
    while True:
        try:
            messages = r.xreadgroup(
                LOGO_GROUP, worker_id,
                {VEHICLE_JOBS_STREAM: ">"}, 
                count=1, block=BLOCK_TIME
            )
            
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    job_id = fields.get("job_id")
                    vehicle_type = fields.get("vehicle_type")
                    frame_path = fields.get("frame_path")
                    
                    print(f"Logo processing job: {job_id} ({vehicle_type})")
                    
                    # Only process cars
                    if should_worker_process("logo", vehicle_type):
                        try:
                            result = process_logo(frame_path)
                            
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "worker": "logo",
                                "result": result,
                                "status": "ok"
                            })
                            
                            print(f"Logo completed: {job_id} -> {result}")
                            r.xack(VEHICLE_JOBS_STREAM, LOGO_GROUP, msg_id)
                            
                        except Exception as e:
                            print(f"Logo failed for {job_id}: {e}")
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "worker": "logo",
                                "result": "",
                                "status": "error", 
                                "error": str(e)
                            })
                    else:
                        print(f"Logo skipping {vehicle_type} (cars only)")
                        r.xack(VEHICLE_JOBS_STREAM, LOGO_GROUP, msg_id)
                        
        except Exception as e:
            print(f"Logo worker error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    logo_worker()
