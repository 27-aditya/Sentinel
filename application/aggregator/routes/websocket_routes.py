from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter()

# These will be injected from main
SYSTEM_READY = None
manager = None

def init_globals(system_ready_ref, manager_ref):
    global SYSTEM_READY, manager
    SYSTEM_READY = system_ready_ref
    manager = manager_ref

@router.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    # Wait until system is ready before accepting connections
    max_wait = 60  # Maximum 60 seconds wait
    waited = 0
    while not SYSTEM_READY["ready"] and waited < max_wait:
        await asyncio.sleep(0.5)
        waited += 0.5
    
    if not SYSTEM_READY["ready"]:
        await websocket.close(code=1008, reason="System not ready")
        print("WebSocket connection rejected: System not ready")
        return
    
    await manager.connect(websocket)
    print("WebSocket client connected successfully")
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("A client disconnected.")


@router.post("/internal/system-ready")
async def mark_system_ready():
    """Internal endpoint called by orchestrator when ingress is ready"""
    SYSTEM_READY["ready"] = True
    print("✓ System marked as READY - WebSocket connections now allowed")
    return {"status": "ready"}


@router.get("/api/system/status")
async def get_system_status():
    """Check if system is ready for WebSocket connections"""
    return {
        "ready": SYSTEM_READY["ready"],
        "websocket_enabled": SYSTEM_READY["ready"]
    }
