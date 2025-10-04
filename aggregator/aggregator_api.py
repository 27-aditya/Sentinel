import asyncio
import threading
import time
from collections import defaultdict
from fastapi import FastAPI, HTTPException
import psycopg2
from db_redis.sentinel_redis_config import *

# Simple database connection
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="sentinel",
        user="sentinel_user", 
        password="admin"
    )

class ResultAggregator:
    def __init__(self):
        self.pending_jobs = defaultdict(dict)  # job_id -> {worker: result}
        self.r = get_redis_connection()
        
    def save_to_database(self, job_data):
        """Save completed job to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO vehicles (vehicle_id, vehicle_type, full_image_path, plate_image_path, 
                                color, vehicle_number, model, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            job_data.get("vehicle_id"),
            job_data.get("vehicle_type"),
            job_data.get("frame_path"),
            job_data.get("plate_path"),
            job_data.get("color", ""),
            job_data.get("vehicle_number", ""),
            job_data.get("model", ""),
            "completed"
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    def process_results(self):
        """Main aggregator loop"""
        print("Aggregator started")
        
        while True:
            try:
                messages = self.r.xreadgroup(
                    AGGREGATOR_GROUP, "aggregator_1",
                    {VEHICLE_RESULTS_STREAM: ">"}, 
                    count=10, block=1000
                )
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        job_id = fields.get("job_id")
                        worker = fields.get("worker")
                        result = fields.get("result")
                        status = fields.get("status")
                        
                        print(f"Received result: {job_id} from {worker} -> {result}")
                        
                        # Store result
                        if job_id not in self.pending_jobs:
                            # Get original job details
                            self.pending_jobs[job_id] = {"results": {}}
                            
                        self.pending_jobs[job_id]["results"][worker] = result
                        
                        # Get vehicle type from job_id (assuming format: car_123_uuid)
                        vehicle_type = job_id.split("_")[0]
                        expected_workers = get_expected_workers(vehicle_type)
                        
                        # Check if all results are in
                        received_workers = list(self.pending_jobs[job_id]["results"].keys())
                        if set(received_workers) >= set(expected_workers):
                            print(f"All results received for {job_id}: {received_workers}")
                            
                            # Prepare data for database
                            results = self.pending_jobs[job_id]["results"]
                            job_data = {
                                "vehicle_id": job_id.split("_")[1],  # Extract ID
                                "vehicle_type": vehicle_type,
                                "frame_path": f"keyframes/{job_id}.jpg",  # Approximate
                                "plate_path": f"processed_keyframes/{job_id}_plate.jpg",
                                "color": results.get("color", ""),
                                "vehicle_number": results.get("ocr", ""),
                                "model": results.get("logo", "")
                            }
                            
                            # Save to database
                            self.save_to_database(job_data)
                            print(f"Saved {job_id} to database")
                            
                            # Send ACK (optional for now)
                            self.r.xadd(VEHICLE_ACK_STREAM, {
                                "job_id": job_id,
                                "status": "completed"
                            })
                            
                            # Clean up
                            del self.pending_jobs[job_id]
                        
                        # Acknowledge message
                        self.r.xack(VEHICLE_RESULTS_STREAM, AGGREGATOR_GROUP, msg_id)
                        
            except Exception as e:
                print(f"Aggregator error: {e}")
                time.sleep(1)

# FastAPI app
app = FastAPI(title="Sentinel Vehicle API")

@app.get("/vehicles")
async def get_vehicles():
    """Get all processed vehicles"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT vehicle_id, vehicle_type, color, vehicle_number, model, timestamp
        FROM vehicles 
        ORDER BY timestamp DESC LIMIT 100
    """)
    
    vehicles = []
    for row in cursor.fetchall():
        vehicles.append({
            "vehicle_id": row[0],
            "vehicle_type": row[1], 
            "color": row[2],
            "vehicle_number": row[3],
            "model": row[4],
            "timestamp": row[5]
        })
    
    cursor.close()
    conn.close()
    return vehicles

@app.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    """Get specific vehicle"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    cursor.close()
    conn.close()
    
    return {
        "id": row[0],
        "vehicle_id": row[1],
        "vehicle_type": row[2],
        "full_image_path": row[3],
        "plate_image_path": row[4],
        "color": row[5],
        "vehicle_number": row[6],
        "model": row[7],
        "timestamp": row[8],
        "status": row[9]
    }

# Start aggregator in background thread
aggregator = ResultAggregator()
aggregator_thread = threading.Thread(target=aggregator.process_results, daemon=True)
aggregator_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
