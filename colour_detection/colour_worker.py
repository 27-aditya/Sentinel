import time
import random
import signal
import sys
import threading
from db_redis.sentinel_redis_config import *

shutdown_event = threading.Event()

def handle_shutdown(signum, frame):
    print(f"\nReceived signal {signum}, shutting down Colour Worker gracefully...")
    shutdown_event.set()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def process_colour(frame_path):
    """Dummy colour detection - replace with real colour detection logic"""
    time.sleep(random.uniform(0.3, 1.5))
    colours = ["red", "blue", "white", "black", "silver", "green", "yellow"]
    return random.choice(colours)

def colour_worker():
    r = get_redis_connection()
    worker_id = "colour_worker_1"

    print(f"[Colour] Worker started: {worker_id}")

    while not shutdown_event.is_set():
        try:
            messages = r.xreadgroup(
                COLOUR_GROUP, worker_id,
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

                    print(f"[Colour] Processing job: {job_id} ({vehicle_type})")

                    if should_worker_process("colour", vehicle_type):
                        try:
                            result = process_colour(frame_path)
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "vehicle_id": fields.get("vehicle_id"),
                                "worker": "colour",
                                "result": result,
                                "status": "ok"
                            })
                            print(f"[Colour] Completed: {job_id} -> {result}")
                            r.xack(VEHICLE_JOBS_STREAM, COLOUR_GROUP, msg_id)
                        except Exception as e:
                            print(f"[Colour] Failed for {job_id}: {e}")
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "worker": "colour",
                                "result": "",
                                "status": "error",
                                "error": str(e)
                            })
                    else:
                        print(f"[Colour] Skipping {vehicle_type} (not in scope)")
                        r.xack(VEHICLE_JOBS_STREAM, COLOUR_GROUP, msg_id)

        except Exception as e:
            print(f"[Colour] Worker error: {e}")
            time.sleep(1)

    print("[Colour] Shutdown complete.")

if __name__ == "__main__":
    colour_worker()