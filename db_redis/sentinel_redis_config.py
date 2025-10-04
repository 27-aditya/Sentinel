# Sentinel Redis Configuration
import redis
import os

# Redis Connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Redis connection instance
def get_redis_connection():
    """Get Redis connection with decode_responses=True for strings"""
    return redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        db=REDIS_DB, 
        decode_responses=True
    )

# Stream Names
VEHICLE_JOBS_STREAM = "vehicle_jobs"
VEHICLE_RESULTS_STREAM = "vehicle_results"
VEHICLE_ACK_STREAM = "vehicle_ack"

# Consumer Groups
OCR_GROUP = "ocr_workers"
COLOR_GROUP = "color_workers"
LOGO_GROUP = "logo_workers"
AGGREGATOR_GROUP = "aggregator" 
INGEST_GROUP = "ingest"

# Processing Configuration
BATCH_SIZE = 10          # Messages per batch
BLOCK_TIME = 1000        # ms to block on XREADGROUP
ACK_TIMEOUT = 30000      # 30 seconds
MAX_RETRIES = 3

# Worker Types
WORKER_TYPES = {
    "ocr": ["car", "bike", "bus", "auto"],      # OCR works on all vehicles
    "color": ["car"],                            # Color only for cars
    "logo": ["car"]                              # Logo/model only for cars
}

def get_expected_workers(vehicle_type):
    """Get list of workers expected for a vehicle type"""
    if vehicle_type == "car":
        return ["ocr", "color", "logo"] 
    else:
        return ["ocr"]

def should_worker_process(worker_type, vehicle_type):
    """Check if worker should process this vehicle type"""
    return vehicle_type in WORKER_TYPES.get(worker_type, [])
