Input: 1 Camera stream per system
Output: {Id: vehicleId, Image: fullImage, Image: plateImage, String: colour, String: vehicleNumber, String: model}
### Architecture Diagram
   ┌────────────┐
   │  Camera    │
   │ Ingest     │
   │ (Process 1)│
   └─────┬──────┘
         │
         ▼
   ┌──────────────────┐
   │ Redis Stream     │
   │ "vehicle_jobs"   │
   └─────┬──────┬─────┘
         │      │
 ┌───────▼─┐  ┌─▼────────┐  ┌───────────┐
 │ OCR     │  │ Colour   │  │ Logo/Model│
 │ Worker  │  │ Worker   │  │ Worker    │
 │(Proc 2) │  │(Proc 3)  │  │(Proc 4)   │
 └───────┬─┘  └─┬────────┘  └───────┬───┘
         │      │                   │
         └──────┴───────────────────┘
                  results
	                 │
                     ▼
            ┌─────────────────────┐
            │ Aggregator + API    │
            │ (FastAPI Proc 5)    │
            │  - listens to       │
            │    "vehicle_results"│  
            │  - writes DB        │
            │  - serves API       │
            └─────────────────────┘
### **Camera Ingest (Process 1)**
- Reads RTSP stream (`cv2.VideoCapture`)
- Runs YOLOv8 for vehicle detection + tracking (with DeepSORT/ByteTrack).
- For each **unique vehicle**, saves a **keyframe to disk**.
- Enqueues a job into Redis Stream `vehicle_jobs` with:
```
{
  "job_id": "<vehicle_type>_<uuid>",
  "path": "keyframes/car_12_frame234.jpg",
  "vehicle_type": "car" | "bus" | "auto" | "bike",
  "timestamp": "...",
}
```
### **Workers (Process 2–4)**
- **OCR Worker** → always runs (needed for all 4 classes).
- **Color Worker** → only runs if vehicle is `car`.
- **Logo/Model Worker** → only runs if vehicle is `car`.
Each worker:
- Subscribes to `vehicle_jobs`.
- Processes **only the relevant jobs**.
- Publishes results into `vehicle_results` stream:

```
{
  "job_id": "<worker>_<uuid>",
  "worker": "ocr" | "color" | "logo",
  "result": "...",
  "status": "ok" | "error"
}
```
### **Aggregator + API (Process 5)**
- Subscribes to `vehicle_results`.
- Collects partial results for each `job_id`.
- Rules:
    - **Car**: expect 3 results → {OCR, Color, Logo}.
    - **Bus/Auto/Bike**: expect 1 result → {OCR}.
- Uses a **timeout (30s)**:
    - If not all required results arrive → republishes the missing parts as **retry requests**.
    - If still missing after retry → mark as failed.****
- Once all required results are in:
    - Sends **ack** back to ingest (`vehicle_ack` stream or `XACK` if using consumer groups).
    - Writes consolidated result into DB: 
	    - {Id: vehicleId, Image: fullImage, Image: plateImage, String: colour, String: vehicleNumber, String: model}
    - Exposes via FastAPI API for retrieval.
### Message Flow (with ACKs)
1. **Ingest → `vehicle_jobs`**: creates a job.
2. **Workers → `vehicle_results`**: return results.
3. **Aggregator**: waits for required results.
    - If complete → pushes `ack` to `vehicle_ack`. 
    - If incomplete after 30s → pushes retry to `vehicle_jobs`.

Ingest **only deletes job from Redis** (or marks as processed) **after it receives ACK** from aggregator.  
This ensures jobs are never dropped, and keyframes remain on disk for reprocessing if needed.