from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse

router = APIRouter()

# These will be injected from main
generate_frames = None
templates = None
LOCATION = None
HLS_OUTPUT_DIR = None

def init_stream(frames_func, templates_ref, location, hls_dir=None):
    global generate_frames, templates, LOCATION, HLS_OUTPUT_DIR
    generate_frames = frames_func
    templates = templates_ref
    LOCATION = location
    HLS_OUTPUT_DIR = hls_dir

@router.get("/stream_feed")
async def stream_feed():
    """MJPEG streaming endpoint for RTSP feed."""
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/stream", response_class=HTMLResponse)
async def stream_page(request: Request):
    """Render a live stream viewer page."""
    return templates.TemplateResponse("stream.html", {"request": request, "location": LOCATION})

# TEMP HLS stream endpoint
@router.get("/hls/stream.m3u8")
async def hls_playlist():
    """Serve HLS playlist file"""
    if HLS_OUTPUT_DIR:
        m3u8_file = HLS_OUTPUT_DIR / "stream.m3u8"
        if m3u8_file.exists():
            return FileResponse(
                str(m3u8_file),
                media_type="application/vnd.apple.mpegurl",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    return {"error": "HLS stream not available"}

# TEMP HLS segment endpoint
@router.get("/hls/{segment_name}")
async def hls_segment(segment_name: str):
    """Serve HLS video segments (.ts files)"""
    if HLS_OUTPUT_DIR:
        segment_file = HLS_OUTPUT_DIR / segment_name
        if segment_file.exists():
            return FileResponse(
                str(segment_file),
                media_type="video/MP2T",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                }
            )
    return {"error": "Segment not found"}