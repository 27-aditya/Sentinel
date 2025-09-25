import subprocess
import sys

def mp4_to_rtsp(input_file: str, rtsp_url: str, loop: bool = True):
    """
    Streams an MP4 file as an RTSP stream using FFmpeg.

    Args:
        input_file (str): Path to the .mp4 file.
        rtsp_url (str): RTSP output URL, e.g. "rtsp://127.0.0.1:8554/stream".
        loop (bool): Whether to loop the video endlessly.
    """
    # ffmpeg command
    cmd = [
        "ffmpeg",
        "-re",                      # read input at native frame rate
        "-stream_loop", "-1" if loop else "0",
        "-i", input_file,           # input file
        "-c:v", "libx264",          # video codec
        "-preset", "veryfast",      # encoding speed
        "-tune", "zerolatency",     # low latency
        "-c:a", "aac",              # audio codec
        "-f", "rtsp",               # output format
        rtsp_url
    ]

    print("Running command:", " ".join(cmd))
    subprocess.run(cmd)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python mp4_to_rtsp.py input.mp4 rtsp://127.0.0.1:8554/stream")
        sys.exit(1)

    input_file = sys.argv[1]
    rtsp_url = sys.argv[2]

    mp4_to_rtsp(input_file, rtsp_url)
