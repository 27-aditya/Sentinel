import subprocess
import time
import cv2
import sys
import os
import signal

# Paths
MEDIA_FILE = "in1.mp4"
MEDIAMTX_BINARY = "./mediamtx"  # path to MediaMTX binary
RTSP_URL = "rtsp://127.0.0.1:8554/stream"

def start_mediamtx():
    """Start MediaMTX server."""
    return subprocess.Popen([MEDIAMTX_BINARY, "mediamtx.yml"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_stream():
    """Start streaming MP4 to RTSP using FFmpeg."""
    cmd = [
        "ffmpeg",
        "-re",
        "-stream_loop", "-1",
        "-i", MEDIA_FILE,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-c:a", "aac",
        "-f", "rtsp",
        RTSP_URL
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def view_stream():
    """Open the RTSP stream with OpenCV."""
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        print("Error: Cannot open video stream")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Camera Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        # 1️⃣ Start MediaMTX
        print("Starting MediaMTX server...")
        mediamtx_proc = start_mediamtx()
        time.sleep(1)  # wait a bit for the server to initialize

        # 2️⃣ Start streaming MP4
        print("Starting MP4 stream...")
        ffmpeg_proc = start_stream()
        time.sleep(2)  # give it a second to push first frames

        # 3️⃣ Open OpenCV viewer
        print("Opening OpenCV viewer...")
        view_stream()

    finally:
        # Cleanup processes
        print("Stopping streaming and server...")
        if ffmpeg_proc:
            ffmpeg_proc.terminate()
        if mediamtx_proc:
            mediamtx_proc.terminate()
