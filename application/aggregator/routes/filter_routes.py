from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime

router = APIRouter()
get_db_connection: Callable = None

def init_db(db_connection_func: Callable):
    global get_db_connection
    get_db_connection = db_connection_func

# To populate the filters in the front end
@router.get("/api/filters", response_model=Dict[str, List[Dict[str, Any]]])
async def get_filter_options():
    """
    Fetches all available filter options (locations, types, colors)
    for the frontend dropdowns by querying the lookup tables.
    """
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch Locations
        cursor.execute("SELECT id, name FROM locations ORDER BY name;")
        locations = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

        # Fetch Vehicle Types
        cursor.execute("SELECT id, name FROM vehicle_types ORDER BY name;")
        vehicle_types = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

        # Fetch Colors
        cursor.execute("SELECT id, name, hex_code FROM colors ORDER BY name;")
        colors = [{"id": row[0], "name": row[1], "hex_code": row[2]} for row in cursor.fetchall()]
        
        return {
            "locations": locations,
            "vehicle_types": vehicle_types,
            "colors": colors
        }
    finally:
        if conn:
            cursor.close()
            conn.close()

# get filtered records from the db  
@router.get("/api/search")
async def search_vehicles(
    location: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    color: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    plate_query: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    Powerful endpoint for searching and filtering vehicles with pagination.
    This endpoint dynamically builds a SQL query to let the database do the heavy lifting.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # --- Dynamically build the SQL query ---
        query_base = "SELECT vehicle_id, vehicle_type, keyframe_url, plate_url, color, color_hex, vehicle_number, model, location, timestamp FROM vehicles WHERE 1=1"
        count_base = "SELECT COUNT(*) FROM vehicles WHERE 1=1"
        params = []
        
        # Build WHERE clauses based on provided filters
        where_clauses = ""
        if location:
            where_clauses += " AND location = %s"
            params.append(location)
        if start_date:
            where_clauses += " AND timestamp >= %s"
            params.append(start_date)
        if end_date:
            where_clauses += " AND timestamp <= %s"
            params.append(end_date)
        if color:
            where_clauses += " AND color = %s"
            params.append(color)
        if vehicle_type:
            where_clauses += " AND vehicle_type = %s"
            params.append(vehicle_type)
        if plate_query:
            # Use ILIKE for case-insensitive partial matching. This is fast if indexed.
            where_clauses += " AND vehicle_number ILIKE %s"
            params.append(f"%{plate_query}%")

        # --- Get Total Count for Pagination ---
        count_query = count_base + where_clauses
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()[0]

        # --- Get Paginated Data ---
        offset = (page - 1) * page_size
        data_query = query_base + where_clauses + " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
        
        cursor.execute(data_query, tuple(params + [page_size, offset]))
        
        vehicles = [
            {
                "vehicle_id": row[0], "vehicle_type": row[1], "keyframe_url": row[2],
                "plate_url": row[3], "color": row[4], "color_hex": row[5],
                "vehicle_number": row[6], "model": row[7], "location": row[8],
                "timestamp": row[9],
            }
            for row in cursor.fetchall()
        ]

        return {
            "vehicles": vehicles, 
            "total_count": total_count, 
            "page": page, 
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }

    except Exception as e:
        print(f"Error during vehicle search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during search.")
    finally:
        if conn:
            cursor.close()
            conn.close()

