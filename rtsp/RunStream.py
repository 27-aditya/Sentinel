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


if __name__ == "__main__":
    try:
        # Start MediaMTX
        print("Starting MediaMTX server...")
        mediamtx_proc = start_mediamtx()
        time.sleep(1)

        # Start streaming MP4
        print("Starting MP4 stream...")
        ffmpeg_proc = start_stream()
        time.sleep(2)

        # Keep running
        print("Stream active. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Cleanup processes
        if ffmpeg_proc:
            ffmpeg_proc.terminate()
        if mediamtx_proc:
            mediamtx_proc.terminate()
