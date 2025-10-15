from fastapi import APIRouter, HTTPException

router = APIRouter()

# This will be injected from main
get_db_connection = None

def init_db(db_func):
    global get_db_connection
    get_db_connection = db_func

@router.get("/api/vehicles")
async def get_vehicles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vehicle_id, vehicle_type, keyframe_url, plate_url, color, color_hex, vehicle_number, model, location, timestamp
        FROM vehicles 
        ORDER BY timestamp DESC 
        LIMIT 100
    """)
    vehicles = [
        {
            "vehicle_id": row[0],
            "vehicle_type": row[1],
            "keyframe_url": row[2],
            "plate_url": row[3],
            "color": row[4],
            "color_hex": row[5],
            "vehicle_number": row[6],
            "model": row[7],
            "location": row[8],
            "timestamp": row[9],
        }
        for row in cursor.fetchall()
    ]
    cursor.close()
    conn.close()
    return vehicles


@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
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
        "keyframe_url": row[3],
        "plate_url": row[4],
        "color": row[5],
        "color_hex": row[6],
        "vehicle_number": row[7],
        "model": row[8],
        "location": row[9],
        "timestamp": row[10],
        "status": row[11]
    }
