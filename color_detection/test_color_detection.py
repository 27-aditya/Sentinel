import os
import cv2
import numpy as np
import glob
import webcolors
from collections import Counter
from sklearn.cluster import KMeans

# Car color categories with comprehensive CSS color mapping
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
        'darkslategray',
        'darkslategrey', 'slategray', 'slategrey', 'lightslategray', 'lightslategrey'
    ],
    'white': [
        'white', 'whitesmoke', 'snow', 'ivory', 'floralwhite', 'ghostwhite',
        'honeydew', 'mintcream', 'azure', 'aliceblue', 'lavenderblush',
        'seashell', 'beige', 'oldlace', 'linen', 'antiquewhite', 'lightgray', 'lightgrey', 'gainsboro', 'silver',
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
    
    # Get CSS3 colors - correct attribute for modern webcolors
    try:
        # Try new API first
        for name in webcolors.names('css3'):
            try:
                rgb = webcolors.name_to_rgb(name, spec='css3')
                css_colors[name] = rgb
            except ValueError:
                continue
    except AttributeError:
        # Fallback for older versions
        try:
            import webcolors._definitions as defs
            for name, hex_val in defs.CSS3_NAMES_TO_HEX.items():
                rgb = webcolors.hex_to_rgb(hex_val)
                css_colors[name] = rgb
        except (AttributeError, ImportError):
            # Manual fallback with common colors
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
    
    return 'gray'  # Default fallback

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
    
    # Filter out very dark and very bright pixels
    mask = np.all(pixels > [25, 25, 25], axis=1) & np.all(pixels < [230, 230, 230], axis=1)
    filtered_pixels = pixels[mask]
    
    if len(filtered_pixels) < 50:
        filtered_pixels = pixels
    
    # Use fewer clusters for better results
    n_clusters = min(k, len(filtered_pixels))
    if n_clusters < 1:
        return [np.mean(pixels, axis=0)]
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(filtered_pixels)
    
    colors = kmeans.cluster_centers_
    labels = kmeans.labels_
    counts = Counter(labels)
    
    # Sort by frequency
    sorted_colors = [colors[i] for i in sorted(counts, key=counts.get, reverse=True)]
    return sorted_colors

def detect_car_color(image_path):
    """Main color detection function"""
    try:
        image = cv2.imread(image_path)
        if image is None:
            return "unknown", [0, 0, 0], "#000000", "unknown"
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cropped = crop_car_body(image_rgb)
        
        # Get dominant colors
        dominant_colors = extract_dominant_colors(cropped, k=3)
        
        if not dominant_colors:
            return "unknown", [0, 0, 0], "#000000", "unknown"
        
        # Use the most dominant color
        primary_color = dominant_colors[0]
        
        # Special handling for very bright/dark colors
        brightness = np.mean(primary_color)
        if brightness < 30:
            return "black", primary_color.astype(int), rgb_to_hex(primary_color), "black"
        elif brightness > 220:
            return "white", primary_color.astype(int), rgb_to_hex(primary_color), "white"
        
        # Find closest CSS color
        css_name = closest_css_color(primary_color)
        car_color = map_to_car_color(css_name)
        hex_value = rgb_to_hex(primary_color)
        
        print(f"    RGB: {primary_color.astype(int)} -> CSS: {css_name} -> Car: {car_color}")
        
        return car_color, primary_color.astype(int), hex_value, css_name
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return "unknown", [0, 0, 0], "#000000", "unknown"

def save_processed_image(image_path, color_name, rgb_values, hex_value, css_name, output_dir="output"):
    """Save processed image with color overlay"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        image = cv2.imread(image_path)
        if image is None:
            return
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cropped = crop_car_body(image_rgb)
        overlay = image_rgb.copy()
        
        # Create color overlay
        rgb_tuple = tuple(int(x) for x in rgb_values)
        cv2.rectangle(overlay, (10, 10), (400, 120), rgb_tuple, -1)
        
        # Add text
        cv2.putText(overlay, f"Car: {color_name}", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(overlay, f"CSS: {css_name}", (20, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(overlay, f"RGB: {rgb_tuple}", (20, 85),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(overlay, f"HEX: {hex_value}", (20, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Save images
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        
        cv2.imwrite(f"{output_dir}/{name}_cropped{ext}", 
                   cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))
        cv2.imwrite(f"{output_dir}/{name}_result{ext}", 
                   cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
        
    except Exception as e:
        print(f"Error saving processed image: {e}")

def main():
    """Main processing function"""
    input_dir = "in"
    
    if not os.path.exists(input_dir):
        print(f"Create '{input_dir}' directory and put test images there")
        return
    
    # Find image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(input_dir, ext)))
    
    if not image_files:
        print(f"No images found in '{input_dir}'")
        return
    
    print(f"Found {len(image_files)} images to process")
    print("Car Colors: red, blue, green, yellow, brown, black, white, gray")
    print("="*60)
    
    results = []
    
    for image_path in image_files:
        filename = os.path.basename(image_path)
        print(f"\nProcessing: {filename}")
        
        car_color, rgb_values, hex_value, css_name = detect_car_color(image_path)
        results.append((filename, car_color, rgb_values, hex_value, css_name))
        
        print(f"  RESULT: {car_color} (RGB: {rgb_values}, HEX: {hex_value})")
        save_processed_image(image_path, car_color, rgb_values, hex_value, css_name)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    
    color_counts = Counter([r[1] for r in results])
    for color, count in color_counts.most_common():
        print(f"{color:10} : {count:2} images")
    
    print(f"\nProcessed images saved to 'output' directory")

if __name__ == "__main__":
    main()
