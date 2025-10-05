#!/usr/bin/env python3
import subprocess
import redis
import sys
import time

# Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Stream names for Sentinel architecture
STREAMS = {
    "VEHICLE_JOBS": "vehicle_jobs",
    "VEHICLE_RESULTS": "vehicle_results", 
    "VEHICLE_ACK": "vehicle_ack"
}

# Consumer groups
CONSUMER_GROUPS = {
    "vehicle_jobs": ["ocr_workers", "colour_workers", "logo_workers"],
    "vehicle_results": ["aggregator"],
    "vehicle_ack": ["ingest"]
}

def setup_streams_and_groups():
    """Create Redis streams and consumer groups for Sentinel"""
    print("Setting up Redis streams and consumer groups...")
    
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        
        # Create streams and consumer groups
        for stream_name, groups in CONSUMER_GROUPS.items():
            print(f"Setting up stream: {stream_name}")
            
            for group in groups:
                try:
                    # Create consumer group (will create stream if needed)
                    r.xgroup_create(stream_name, group, id='0', mkstream=True)
                    print(f"  Created consumer group '{group}' for stream '{stream_name}'")
                except redis.ResponseError as e:
                    if "BUSYGROUP" in str(e):
                        print(f"  Consumer group '{group}' already exists for '{stream_name}'")
                    else:
                        print(f"  Error creating group '{group}': {e}")
        
        print("All streams and consumer groups configured")
        return True
        
    except Exception as e:
        print(f"Failed to setup streams: {e}")
        return False

def cleanup_streams():
    """Clean up test data and optionally remove all streams."""
    print("Cleaning up test messages and streams...")

    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

        # Delete only test messages
        for stream in STREAMS.values():
            try:
                info = r.xinfo_stream(stream)
                if info["length"] > 0:
                    r.delete(stream)
                    print(f"  Deleted stream '{stream}' and its data.")
            except redis.ResponseError:
                print(f"  Stream '{stream}' does not exist, skipping.")
        
        print("Cleanup complete.")
        return True
    except Exception as e:
        print(f"Cleanup failed: {e}")
        return False

def test_streams():
    """Test Redis streams functionality"""
    print("Testing Redis streams...")
    
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        
        # Test 1: Add a test message to vehicle_jobs
        test_job = {
            "job_id": "test_job_001",
            "vehicle_type": "car", 
            "path": "test/path.jpg",
            "timestamp": "2025-10-04T16:20:00"
        }
        
        msg_id = r.xadd("vehicle_jobs", test_job)
        print(f"  Added test job to vehicle_jobs: {msg_id}")
        
        # Test 2: Read from OCR consumer group
        messages = r.xreadgroup("ocr_workers", "test_consumer", {"vehicle_jobs": ">"}, count=1)
        if messages and len(messages[0][1]) > 0:
            print("  Successfully read message from ocr_workers group")
            r.xack("vehicle_jobs", "ocr_workers", messages[0][1][0][0])
            print("  Message acknowledged")
        
        # Test 3: Test that the same job appears in other groups
        messages = r.xreadgroup("colour_workers", "test_consumer", {"vehicle_jobs": ">"}, count=1)
        if messages and len(messages[0][1]) > 0:
            print("  Successfully read same message from colour_workers group")
            r.xack("vehicle_jobs", "colour_workers", messages[0][1][0][0])
        
        messages = r.xreadgroup("logo_workers", "test_consumer", {"vehicle_jobs": ">"}, count=1)
        if messages and len(messages[0][1]) > 0:
            print("  Successfully read same message from logo_workers group")
            r.xack("vehicle_jobs", "logo_workers", messages[0][1][0][0])
        
        # Test 4: Add test result
        test_result = {
            "job_id": "ocr_test_001",
            "worker": "ocr",
            "result": "ABC123",
            "status": "ok"
        }
        
        result_id = r.xadd("vehicle_results", test_result)
        print(f"  Added test result to vehicle_results: {result_id}")
        
        # Test 5: Check stream info
        for stream in STREAMS.values():
            try:
                info = r.xinfo_stream(stream)
                print(f"  Stream '{stream}': {info['length']} messages, {info['groups']} groups")
            except redis.ResponseError:
                print(f"  Stream '{stream}': No messages yet")
        
        print("All stream tests passed")
        return True
        
    except Exception as e:
        print(f"Stream test failed: {e}")
        return False

def main():
    print("Setting up Redis for Sentinel Architecture")
    print("=" * 50)
    
    # Test Redis connection first
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        r.ping()
        print("Redis connection verified")
    except Exception as e:
        print(f"Cannot connect to Redis: {e}")
        print("Make sure Redis is running: sudo systemctl start redis-server")
        sys.exit(1)
    
    # Setup streams and consumer groups
    if not setup_streams_and_groups():
        print("Failed to setup streams")
        sys.exit(1)
    
    # Test functionality
    if not test_streams():
        print("Stream tests failed")
        sys.exit(1)

    # cleanup_streams()
    
    print("\n" + "="*60)
    print("Redis setup for Sentinel completed successfully!")
    print("="*60)
    print(f"Redis Server: {REDIS_HOST}:{REDIS_PORT}")
    print(f"Database: {REDIS_DB}")
    print("\nStreams created:")
    for name, stream in STREAMS.items():
        print(f"  {name}: {stream}")
    
    print("\nConsumer Groups:")
    for stream, groups in CONSUMER_GROUPS.items():
        print(f"  {stream}: {', '.join(groups)}")

if __name__ == "__main__":
    main()
