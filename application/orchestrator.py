import subprocess
import time
import signal
import sys
import os
import threading
import queue
import requests
import psutil
from db_redis.sentinel_redis_config import *
from dotenv import load_dotenv

load_dotenv()

class SentinelOrchestrator:
    def __init__(self):
        self.processes = {}
        self.log_queues = {}
        self.r = get_redis_connection()
        self.shutdown_requested = False
        self.shutdown_lock = threading.Lock()
        
        self.location = os.getenv("LOCATION", "DEFAULT_LOCATION")
        self.rtsp_stream = os.getenv("RTSP_STREAM")

        # DB credentials
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_pass = os.getenv("DB_PASS")
        
        if not self.rtsp_stream or self.rtsp_stream.strip() == "":
            print("\nERROR: RTSP_STREAM not found in .env")
            print("   Please set RTSP_STREAM=<your_rtsp_url> before running.")
            sys.exit(1)

        print(f"Orchestrator initialized for location: {self.location}")
        print(f"RTSP Stream: {self.rtsp_stream}")

    def cleanup_redis(self):
        """Flush Redis streams and clean up"""
        print("Cleaning up Redis streams...")
        
        try:
            # Delete all streams
            streams = [VEHICLE_JOBS_STREAM, VEHICLE_RESULTS_STREAM, VEHICLE_ACK_STREAM]
            for stream in streams:
                try:
                    self.r.delete(stream)
                    print(f"  Deleted stream: {stream}")
                except Exception as e:
                    print(f"  Stream {stream} already clean")
            
            # Recreate consumer groups
            consumer_groups = {
                VEHICLE_JOBS_STREAM: ["ocr_workers", "color_workers", "logo_workers"],
                VEHICLE_RESULTS_STREAM: ["aggregator"],
                VEHICLE_ACK_STREAM: ["ingest"]
            }
            
            for stream_name, groups in consumer_groups.items():
                for group in groups:
                    try:
                        self.r.xgroup_create(stream_name, group, id='0', mkstream=True)
                        print(f"  Created consumer group '{group}' for '{stream_name}'")
                    except Exception as e:
                        if "BUSYGROUP" not in str(e):
                            print(f"  Error creating group '{group}': {e}")
            
            print("  Redis cleanup complete")
            
        except Exception as e:
            print(f"Redis cleanup failed: {e}")
            return False
        
        return True
    
    def log_reader(self, process, name, color_code):
        """Read process output and add colored labels"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    timestamp = time.strftime('%H:%M:%S')
                    labeled_line = f"\033[{color_code}m[{name:>12}]\033[0m \033[90m{timestamp}\033[0m | {line.rstrip()}"
                    print(labeled_line)
        except Exception as e:
            print(f"\033[91m[{name:>12}]\033[0m Log reader error: {e}")
    
    def start_process(self, name, command, color_code, cwd=None, extra_env=None):
        """Start a process with colored logging"""
        print(f"Starting {name}...")
        
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = f"{env.get('PYTHONPATH', '')}:."
            env['PYTHONUNBUFFERED'] = '1'  

            if extra_env:
                env.update(extra_env)
            
            process = subprocess.Popen(
                command,
                cwd=cwd or ".",
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[name] = process
            
            log_thread = threading.Thread(
                target=self.log_reader, 
                args=(process, name, color_code),
                daemon=True
            )
            log_thread.start()
            
            print(f"  {name} started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"  Failed to start {name}: {e}")
            return False
    
    def check_process_health(self):
        """Check if all processes are still running"""
        dead_processes = []
        for name, process in self.processes.items():
            if process.poll() is not None:
                dead_processes.append(name)
        return dead_processes
    
    def start_workers(self):
        """Start all worker processes"""
        print("\nStarting Workers...")
        
        workers = [
            ("OCR Worker", ["python3", "ocr/ocr_worker.py"], "92"),
            ("Color Worker", ["python3", "color_detection/color_worker.py"], "94"),
            ("Logo Worker", ["python3", "logo_detection/logo_worker.py"], "95"),
        ]
        
        for name, command, color in workers:
            if not self.start_process(name, command, color):
                return False
            time.sleep(1)
        
        return True
    
    def start_aggregator(self):
        """Start the aggregator + API"""
        print("\nStarting Aggregator + API...")

        if not self.rtsp_stream:
            raise Exception("RTSP_STREAM is missing in environment file (.env). Exiting.")

        if not all([self.db_host, self.db_name, self.db_user, self.db_pass]):
            raise Exception("Database credentials missing in .env. Exiting.")

        aggregator_env = {
            "LOCATION": self.location,
            "RTSP_STREAM": self.rtsp_stream,
            "DB_HOST": self.db_host,
            "DB_PORT": self.db_port,
            "DB_NAME": self.db_name,
            "DB_USER": self.db_user,
            "DB_PASS": self.db_pass
        }

        return self.start_process(
            "Aggregator",
            ["python3", "aggregator/aggregator.py"],
            "93",
            extra_env=aggregator_env
        )
    
    def start_monitor(self):
        """Start the Redis monitor"""
        print("\nStarting Redis Monitor...")
        return self.start_process("Monitor", ["python3", "db_redis/monitor_streams.py"], "96")
    
    def start_ingress(self):
        """Start the ingress process with location + RTSP stream"""
        print(f"\nStarting Ingress for location: {self.location}...")
        
        ingress_env = {
            "LOCATION": self.location,
            "RTSP_STREAM": self.rtsp_stream
        }
        
        success = self.start_process(
            "Ingress",
            ["python3", "ingress/ingress.py"],
            "91",
            extra_env=ingress_env
        )
    
        if success:
            # Wait a moment for ingress to fully initialize
            time.sleep(4)
            process = self.processes.get("Ingress")
            if process and process.poll() is not None:
                print("Ingress failed to start properly (stream error or crash).")
                return False
            
            # Signal the aggregator that system is ready
            try:
                response = requests.post("http://localhost:8000/internal/system-ready", timeout=5)
                if response.status_code == 200:
                    print("✓ Signaled aggregator: System READY for WebSocket connections")
                else:
                    print(f"⚠️ Failed to signal aggregator readiness: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Could not signal aggregator readiness: {e}")
        
        return success

    def monitor_system(self):
        """Monitor system health and show status"""
        print(f"\n{'='*80}")
        print("SENTINEL SYSTEM RUNNING - Press Ctrl+C to stop")
        print(f"{'='*80}")
        
        status_colors = {
            "OCR Worker": "92", "Color Worker": "94", "Logo Worker": "95",
            "Aggregator": "93", "Monitor": "96", "Ingress": "91"
        }
        
        try:
            while True:
                dead = self.check_process_health()
                
                if dead:
                    print(f"\nDead processes detected: {', '.join(dead)}")

                    #  If ingress dies, shut everything down
                    if "Ingress" in dead:
                        print("Ingress process died — shutting down orchestrator and all workers.")
                        self.stop_all()
                        sys.exit(1)
                    
                    break
                
                time.sleep(10)
                alive_count = len([p for p in self.processes.values() if p.poll() is None])
                total_count = len(self.processes)
                
                status_line = f"\033[90m[STATUS]\033[0m {alive_count}/{total_count} processes: "
                for name, process in self.processes.items():
                    color = status_colors.get(name, "37")
                    if process.poll() is None:
                        status_line += f"\033[{color}m●\033[0m "
                    else:
                        status_line += f"\033[91m●\033[0m "
                
                print(status_line)
                
        except KeyboardInterrupt:
            print(f"\n\nShutdown requested...")
            self.stop_all()
            sys.exit(0)
    
    def stop_all(self):
        """Stop all processes gracefully and verify termination"""
        with self.shutdown_lock:
            if self.shutdown_requested:
                return
            self.shutdown_requested = True

        print(f"\n{'='*50}")
        print("Stopping all processes...")

        shutdown_order = ["Ingress", "Monitor", "Aggregator", "Logo Worker", "Color Worker", "OCR Worker"]

        for name in shutdown_order:
            process = self.processes.get(name)
            if not process:
                continue
            
            pid = process.pid
            if process.poll() is None:
                print(f"  Stopping {name} (PID: {pid})...")
                try:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                        print(f"  {name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        print(f"  Force killing {name}...")
                        try:
                            os.killpg(os.getpgid(pid), signal.SIGKILL)
                            process.wait(timeout=5)
                        except Exception:
                            pass
                        print(f"  {name} force stopped")
                except Exception as e:
                    print(f"  Error stopping {name}: {e}")

            if self.is_pid_alive(pid):
                print(f"  ⚠️ PID {pid} for {name} is still alive — killing hard...")
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            
            if not self.is_pid_alive(pid):
                print(f"{name} (PID {pid}) successfully stopped")
            else:
                print(f"{name} (PID {pid}) still running after cleanup")

        print("All processes stopped")

    def is_pid_alive(self, pid):
        return psutil.pid_exists(pid)
    
    def run(self):
        """Main orchestrator flow"""
        print("SENTINEL SYSTEM ORCHESTRATOR")
        print("=" * 80)
        print(f"Location: {self.location}")
        print(f"RTSP Stream: {self.rtsp_stream}")

        if not self.cleanup_redis():
            print("Redis cleanup failed. Exiting.")
            return False
        
        if not self.start_workers():
            print("Worker startup failed. Exiting.")
            self.stop_all()
            return False
        
        time.sleep(2)
        if not self.start_aggregator():
            print("Aggregator startup failed. Exiting.")
            self.stop_all()
            return False
        
        time.sleep(1)
        if not self.start_monitor():
            print("Monitor startup failed. Exiting.")
            self.stop_all()
            return False
        
        time.sleep(3)
        if not self.start_ingress():
            print("Ingress startup failed. Exiting.")
            self.stop_all()
            return False
        
        time.sleep(2)
        self.monitor_system()
        
        self.stop_all()
        return True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\nInterrupt received, shutting down...')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    orchestrator = SentinelOrchestrator()
    
    try:
        orchestrator.run()
    except Exception as e:
        print(f"Orchestrator failed: {e}")
        orchestrator.stop_all()
        sys.exit(1)
