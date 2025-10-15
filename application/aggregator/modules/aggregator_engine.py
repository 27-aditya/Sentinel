import time
import asyncio
import json
import datetime
from collections import defaultdict
from db_redis.sentinel_redis_config import *


class ResultAggregator:
    """Aggregates results from multiple workers and saves to database"""
    
    def __init__(self, manager, loop, db_connection_func):
        """
        Args:
            manager: WebSocket ConnectionManager instance
            loop: asyncio event loop for broadcasting
            db_connection_func: Function to get database connection
        """
        self.pending_jobs = defaultdict(dict)
        self.r = get_redis_connection()
        self.manager = manager
        self.loop = loop
        self.get_db_connection = db_connection_func


    def construct_keyframe_url(self, vehicle_id, location):
        """Construct keyframe URL from vehicle_id and location"""
        try:
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            keyframe_url = f"http://localhost:8000/static/{location}/{current_date}/keyframes/{vehicle_id}.jpg"
            return keyframe_url
        except Exception as e:
            print(f"Error constructing keyframe URL for {vehicle_id}: {e}")
            return None


    def construct_plate_url(self, vehicle_id, location):
        """Construct plate image URL from vehicle_id and location using CURRENT date"""
        try: 
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            plate_url = f"http://localhost:8000/static/{location}/{current_date}/plates/{vehicle_id}_plate.jpg"
            return plate_url
        except Exception as e:
            print(f"Error constructing plate URL for {vehicle_id}: {e}")
            return None


    def parse_color_result(self, result):
        """Parse color result format: 'color_name|#hex_code'"""
        if '|' in result:
            color_name, hex_code = result.split('|', 1)
            return color_name.strip(), hex_code.strip()
        else:
            return result.strip(), "#000000"


    def extract_location_from_vehicle_id(self, vehicle_id):
        """Extract location from vehicle_id format: uuid_timestamp_vehicle_type_LOCATION"""
        try:
            parts = vehicle_id.split('_')
            if len(parts) >= 4:
                location_parts = parts[4:]
                return '_'.join(location_parts)
            return "UNKNOWN"
        except:
            return "UNKNOWN"


    def extract_timestamp_from_vehicle_id(self, vehicle_id):
        """Extract timestamp from vehicle_id format: uuid_YYYYMMDD_HHMMSS_vehicle_type_LOCATION"""
        try:
            parts = vehicle_id.split('_')
            if len(parts) >= 3:
                date_part = parts[1]
                time_part = parts[2]
                
                year = int(date_part[0:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])
                hour = int(time_part[0:2])
                minute = int(time_part[2:4])
                second = int(time_part[4:6])
                
                dt = datetime.datetime(year, month, day, hour, minute, second)
                return dt.isoformat()
            return None
        except Exception as e:
            print(f"Error extracting timestamp from vehicle_id {vehicle_id}: {e}")
            return None


    def save_to_database(self, job_data):
        """Save completed job to database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO vehicles (vehicle_id, vehicle_type, keyframe_url, plate_url,
                                  color, color_hex, vehicle_number, model, location, timestamp, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            job_data.get("vehicle_id"),
            job_data.get("vehicle_type"),
            job_data.get("keyframe_url"),
            job_data.get("plate_url"),
            job_data.get("color", ""),
            job_data.get("color_hex", "#000000"),
            job_data.get("vehicle_number", ""),
            job_data.get("model", ""),
            job_data.get("location", "UNKNOWN"),
            job_data.get("timestamp"), 
            "completed"
        ))

        conn.commit()
        cursor.close()
        conn.close()
        return job_data

    
    def process_results(self):
        """Main aggregator loop - runs in background thread"""
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
                        vehicle_id = fields.get("vehicle_id")

                        print(f"Received result: {job_id} from {worker} -> {result}")

                        if job_id not in self.pending_jobs:
                            location = fields.get("location", self.extract_location_from_vehicle_id(vehicle_id))
                            timestamp = self.extract_timestamp_from_vehicle_id(vehicle_id)
                            keyframe_url = self.construct_keyframe_url(vehicle_id, location)
                            plate_url = self.construct_plate_url(vehicle_id, location)
                            
                            self.pending_jobs[job_id] = {
                                "results": {},
                                "vehicle_id": vehicle_id,
                                "location": location,
                                "timestamp": timestamp,
                                "keyframe_url": keyframe_url,
                                "plate_url": plate_url
                            }

                        self.pending_jobs[job_id]["results"][worker] = result
                        vehicle_type = job_id.split("_")[0]
                        expected_workers = get_expected_workers(vehicle_type)

                        received_workers = list(self.pending_jobs[job_id]["results"].keys())
                        if set(received_workers) >= set(expected_workers):
                            print(f"All results received for {job_id}: {received_workers}")

                            results = self.pending_jobs[job_id]["results"]
                            stored_vehicle_id = self.pending_jobs[job_id]["vehicle_id"]
                            location = self.pending_jobs[job_id]["location"]
                            timestamp = self.pending_jobs[job_id]["timestamp"]
                            keyframe_url = self.pending_jobs[job_id]["keyframe_url"]
                            plate_url = self.pending_jobs[job_id]["plate_url"]

                            color_result = results.get("color", "unknown|#000000")
                            color_name, color_hex = self.parse_color_result(color_result)

                            job_data = {
                                "vehicle_id": stored_vehicle_id,
                                "vehicle_type": vehicle_type,
                                "keyframe_url": keyframe_url,
                                "plate_url": plate_url,
                                "color": color_name,
                                "color_hex": color_hex,
                                "vehicle_number": results.get("ocr", ""),
                                "model": results.get("logo", ""),
                                "location": location,
                                "timestamp": timestamp
                            }

                            saved_data = self.save_to_database(job_data)
                            print(f"Saved {job_id} to database: vehicle_id: {stored_vehicle_id}")

                            # Broadcast the update
                            asyncio.run_coroutine_threadsafe(
                                self.manager.broadcast(json.dumps(saved_data, default=str)),
                                self.loop
                            )
                            print(f"Scheduled broadcast for {job_id}")

                            self.r.xadd(VEHICLE_ACK_STREAM, {
                                "job_id": job_id,
                                "status": "completed"
                            })

                            del self.pending_jobs[job_id]

                        self.r.xack(VEHICLE_RESULTS_STREAM, AGGREGATOR_GROUP, msg_id)

            except Exception as e:
                print(f"Aggregator error: {e}")
                time.sleep(1)
