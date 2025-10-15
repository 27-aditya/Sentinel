from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

# This will be injected from main
get_db_connection = None

def init_db(db_func):
    global get_db_connection
    get_db_connection = db_func

# Pydantic model for update request
class VehicleNumberUpdate(BaseModel):
    vehicle_number: str

@router.get("/api/vehicles")
async def get_vehicles(limit: int = Query(default=100, ge=1, le=1000)):
    """
    Get recent vehicles from the database.
    
    Args:
        limit: Number of vehicles to return (1-1000, default: 100)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vehicle_id, vehicle_type, keyframe_url, plate_url, color, color_hex, vehicle_number, model, location, timestamp
        FROM vehicles 
        ORDER BY timestamp DESC 
        LIMIT %s
    """, (limit,))
    
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

# Update vehicle number endpoint
@router.patch("/api/vehicles/{vehicle_id}/plate")
async def update_vehicle_plate(vehicle_id: str, update_data: VehicleNumberUpdate):
    """
    Update the vehicle registration number for a specific vehicle.
    
    Args:
        vehicle_id: The unique vehicle identifier
        update_data: Object containing the new vehicle_number
    
    Returns:
        The updated vehicle object
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if vehicle exists
    cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Update the vehicle_number
    cursor.execute("""
        UPDATE vehicles 
        SET vehicle_number = %s 
        WHERE vehicle_id = %s
    """, (update_data.vehicle_number, vehicle_id))
    
    conn.commit()
    
    # Fetch updated vehicle
    cursor.execute("""
        SELECT vehicle_id, vehicle_type, keyframe_url, plate_url, color, color_hex, vehicle_number, model, location, timestamp
        FROM vehicles 
        WHERE vehicle_id = %s
    """, (vehicle_id,))
    
    updated_row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return {
        "vehicle_id": updated_row[0],
        "vehicle_type": updated_row[1],
        "keyframe_url": updated_row[2],
        "plate_url": updated_row[3],
        "color": updated_row[4],
        "color_hex": updated_row[5],
        "vehicle_number": updated_row[6],
        "model": updated_row[7],
        "location": updated_row[8],
        "timestamp": updated_row[9],
    }