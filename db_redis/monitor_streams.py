import redis
import time
from db_redis.sentinel_redis_config import *

def monitor_streams():
    """Monitor all Redis streams"""
    r = get_redis_connection()
    
    print("Sentinel Redis Stream Monitor")
    print("=" * 50)
    
    while True:
        try:
            print(f"\nTimestamp: {time.strftime('%H:%M:%S')}")
            print("-" * 30)
            
            # Monitor each stream
            for stream in [VEHICLE_JOBS_STREAM, VEHICLE_RESULTS_STREAM, VEHICLE_ACK_STREAM]:
                try:
                    info = r.xinfo_stream(stream)
                    groups_info = r.xinfo_groups(stream)
                    
                    print(f"{stream}:")
                    print(f"  Messages: {info['length']}")
                    print(f"  Groups: {len(groups_info)}")
                    
                    for group in groups_info:
                        pending = group['pending']
                        consumers = group['consumers']
                        print(f"    Group '{group['name']}': {pending} pending, {consumers} consumers")
                    
                except redis.ResponseError:
                    print(f"{stream}: Stream does not exist")
            
            time.sleep(20)  # Update every 5 seconds
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_streams()
