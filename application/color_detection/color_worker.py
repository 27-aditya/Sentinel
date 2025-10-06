import time
import signal
import sys
import threading
import cv2
import numpy as np
import webcolors
import os
from collections import Counter
from sklearn.cluster import KMeans
from db_redis.sentinel_redis_config import *

shutdown_event = threading.Event()

def handle_shutdown(signum, frame):
    print(f"\nReceived signal {signum}, shutting down Color Worker gracefully...")
    shutdown_event.set()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# Car color categories with the webcolors return 
CAR_COLOR_MAPPING = {
    'red': [
        'red', 'darkred', 'firebrick', 'crimson', 'indianred', 'lightcoral', 'brown',
        'salmon', 'darksalmon', 'lightsalmon', 'tomato', 'orangered', 'coral', 'saddlebrown',
        'sienna', 'chocolate', 'peru', 'rosybrown',
        'burlywood', 'tan', 'wheat', 'goldenrod', 'darkgoldenrod'
    ],
    'blue': [
        'blue', 'navy', 'darkblue', 'mediumblue', 'royalblue', 'steelblue',
        'dodgerblue', 'deepskyblue', 'skyblue', 'lightskyblue', 'lightblue',
        'powderblue', 'cadetblue', 'cornflowerblue', 'slateblue', 'mediumslateblue'
    ],
    'green': [
        'green', 'darkgreen', 'forestgreen', 'limegreen', 'lime', 'seagreen',
        'mediumseagreen', 'springgreen', 'mediumspringgreen', 'lightgreen',
        'palegreen', 'darkseagreen', 'olive', 'olivedrab', 'darkolivegreen',
        'yellowgreen', 'lawngreen', 'chartreuse', 'greenyellow'
    ],
    'yellow': [
        'yellow', 'gold', 'orange', 'darkorange', 'khaki', 'darkkhaki',
        'palegoldenrod', 'lightgoldenrodyellow', 'lightyellow', 'lemonchiffon',
        'lightcyan', 'moccasin', 'navajowhite', 'peachpuff', 'sandybrown'
    ],
    'gray': [
        'gray', 'grey', 'darkgray', 'darkgrey', 'dimgray', 'dimgrey',
        'darkslategray', 'darkslategrey', 'slategray', 'slategrey', 
        'lightslategray', 'lightslategrey'
    ],
    'white': [
        'white', 'whitesmoke', 'snow', 'ivory', 'floralwhite', 'ghostwhite',
        'honeydew', 'mintcream', 'azure', 'aliceblue', 'lavenderblush',
        'seashell', 'beige', 'oldlace', 'linen', 'antiquewhite', 'lightgray', 
        'lightgrey', 'gainsboro', 'silver'
    ],
    'black': [
        'black', 'darkslategray', 'darkslategrey'
    ]
}

def rgb_to_hex(rgb):
    """Convert RGB to HEX"""
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def get_all_css_colors():
    """Get all CSS color names and their RGB values"""
    css_colors = {}
    try:
        for name in webcolors.names('css3'):
            try:
                rgb = webcolors.name_to_rgb(name, spec='css3')
                css_colors[name] = rgb
            except ValueError:
                continue
    except AttributeError:
        css_colors = {
            'red': (255, 0, 0), 'blue': (0, 0, 255), 'green': (0, 128, 0),
            'yellow': (255, 255, 0), 'orange': (255, 165, 0), 'purple': (128, 0, 128),
            'black': (0, 0, 0), 'white': (255, 255, 255), 'gray': (128, 128, 128),
            'brown': (165, 42, 42), 'pink': (255, 192, 203), 'navy': (0, 0, 128)
        }
    return css_colors

def closest_css_color(rgb):
    """Find closest CSS color name using Euclidean distance"""
    css_colors = get_all_css_colors()
    min_distance = float('inf')
    closest_name = 'gray'
    target_rgb = np.array(rgb)
    
    for name, color_rgb in css_colors.items():
        color_array = np.array(color_rgb)
        distance = np.sqrt(np.sum((target_rgb - color_array) ** 2))
        if distance < min_distance:
            min_distance = distance
            closest_name = name
    
    return closest_name

def map_to_car_color(css_name):
    """Map CSS color name to car color category"""
    css_name_lower = css_name.lower().replace(' ', '')
    
    for car_color, css_names in CAR_COLOR_MAPPING.items():
        if css_name_lower in [name.lower().replace(' ', '') for name in css_names]:
            return car_color
    
    # Fallback mapping for unmapped colors
    if 'pink' in css_name_lower or 'violet' in css_name_lower:
        return 'red'
    elif 'cyan' in css_name_lower or 'teal' in css_name_lower:
        return 'blue'
    elif 'magenta' in css_name_lower or 'fuchsia' in css_name_lower:
        return 'red'
    
    return 'gray'

def crop_car_body(image):
    """Crop car body region"""
    h, w = image.shape[:2]
    top = int(h * 0.30)
    bottom = int(h * 0.65)
    left = int(w * 0.1)
    right = int(w * 0.9)
    return image[top:bottom, left:right]

def extract_dominant_colors(image, k=3):
    """Extract dominant colors using K-means"""
    pixels = image.reshape((-1, 3))
    mask = np.all(pixels > [25, 25, 25], axis=1) & np.all(pixels < [230, 230, 230], axis=1)
    filtered_pixels = pixels[mask]
    
    if len(filtered_pixels) < 50:
        filtered_pixels = pixels
    
    n_clusters = min(k, len(filtered_pixels))
    if n_clusters < 1:
        return [np.mean(pixels, axis=0)]
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(filtered_pixels)
    
    colors = kmeans.cluster_centers_
    labels = kmeans.labels_
    counts = Counter(labels)
    
    sorted_colors = [colors[i] for i in sorted(counts, key=counts.get, reverse=True)]
    return sorted_colors

def detect_red_manually(rgb_color):
    """Manual red detection for dark/muted reds"""
    r, g, b = rgb_color
    if r > g and r > b:
        red_dominance = r - max(g, b)
        if red_dominance > 10 and r > 35:
            return True
    return False

def detect_blue_manually(rgb_color):
    """Manual blue detection for dark/muted blues"""
    r, g, b = rgb_color
    if b > r and b > g:
        blue_dominance = b - max(r, g)
        if blue_dominance > 10 and b > 35:
            return True
    return False

def process_color(frame_path):
    """Real color detection using computer vision"""
    try:
        image = cv2.imread(frame_path)
        if image is None:
            print(f"[Color] Could not load image: {frame_path}")
            return "unknown", "#000000"
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cropped = crop_car_body(image_rgb)
        dominant_colors = extract_dominant_colors(cropped, k=3)
        
        if not dominant_colors:
            return "unknown", "#000000"
        
        primary_color = dominant_colors[0]
        brightness = np.mean(primary_color)
        
        if brightness < 30:
            return "black", rgb_to_hex(primary_color)
        elif brightness > 220:
            return "white", rgb_to_hex(primary_color)
        
        css_name = closest_css_color(primary_color)
        car_color = map_to_car_color(css_name)
        hex_value = rgb_to_hex(primary_color)
        
        # Manual overrides for dark/muted colors that get misclassified as gray
        if car_color == 'gray':
            if detect_red_manually(primary_color):
                print(f"[Color] Manual red override: RGB {primary_color.astype(int)} -> red")
                car_color = 'red'
            elif detect_blue_manually(primary_color):
                print(f"[Color] Manual blue override: RGB {primary_color.astype(int)} -> blue")
                car_color = 'blue'
        
        print(f"[Color] Detected RGB: {primary_color.astype(int)} -> {car_color} ({hex_value})")
        
        return car_color, hex_value
        
    except Exception as e:
        print(f"[Color] Error processing image {frame_path}: {e}")
        return "unknown", "#000000"

def color_worker():
    r = get_redis_connection()
    worker_id = os.environ.get('WORKER_ID', 'color_worker_1')
    
    print(f"[Color] Worker started: {worker_id}")
    
    while not shutdown_event.is_set():
        try:
            messages = r.xreadgroup(
                COLOR_GROUP, worker_id,
                {VEHICLE_JOBS_STREAM: ">"}, 
                count=1, block=BLOCK_TIME
            )
            
            if not messages:
                continue
            
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    job_id = fields.get("job_id")
                    vehicle_type = fields.get("vehicle_type")
                    frame_path = fields.get("frame_path")
                    
                    print(f"[Color] Processing job: {job_id} ({vehicle_type})")
                    
                    if should_worker_process("color", vehicle_type):
                        try:
                            color_name, hex_code = process_color(frame_path)
                            
                            # Return both color name and hex code
                            result = f"{color_name}|{hex_code}"
                            
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "vehicle_id": fields.get("vehicle_id"),
                                "worker": "color",
                                "result": result,
                                "status": "ok"
                            })
                            print(f"[Color] Completed: {job_id} -> {color_name} ({hex_code})")
                            r.xack(VEHICLE_JOBS_STREAM, COLOR_GROUP, msg_id)
                        except Exception as e:
                            print(f"[Color] Failed for {job_id}: {e}")
                            r.xadd(VEHICLE_RESULTS_STREAM, {
                                "job_id": job_id,
                                "vehicle_id": fields.get("vehicle_id"),
                                "worker": "color",
                                "result": "unknown|#000000",
                                "status": "error",
                                "error": str(e)
                            })
                            r.xack(VEHICLE_JOBS_STREAM, COLOR_GROUP, msg_id)
                    else:
                        print(f"[Color] Skipping {vehicle_type} (cars only)")
                        r.xack(VEHICLE_JOBS_STREAM, COLOR_GROUP, msg_id)
        
        except Exception as e:
            print(f"[Color] Worker error: {e}")
            time.sleep(1)
    
    print("[Color] Shutdown complete.")

if __name__ == "__main__":
    color_worker()
