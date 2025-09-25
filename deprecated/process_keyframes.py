import cv2
import os
import numpy as np

def preprocess_for_ocr(image_path):
    """
    Applies image processing techniques to a license plate image for OCR.

    Args:
        image_path (str): The path to the image file.

    Returns:
        numpy.ndarray: The pre-processed image ready for OCR.
    """
    # 1. Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Image not found at {image_path}. Skipping.")
        return None

    # 2. Grayscale Conversion
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 3. Denoising
    denoised_image = cv2.medianBlur(gray_image, 5)
    
    # 4. Binarization (Adaptive Thresholding)
    binary_image = cv2.adaptiveThreshold(
        denoised_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, # Block size
        2   # Constant
    )

    # Deskewing can be added here if needed in future right now the camera angle is sufficiently good such that we can get good ocr results without deskewing

    return binary_image

def process_all_keyframes(input_folder, output_folder):
    """
    Iterates through all images in a folder, processes them, and saves the result.

    Args:
        input_folder (str): The directory containing the original keyframes.
        output_folder (str): The directory to save the processed images.
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Iterate through all files in the input folder
    for filename in os.listdir(input_folder):
        # Check if the file is a JPG image to avoid processing non-image files
        if filename.lower().endswith(('.jpg', '.jpeg')):
            # Construct the full file paths
            input_path = os.path.join(input_folder, filename)
            
            # Process the image
            processed_image = preprocess_for_ocr(input_path)
            
            if processed_image is not None:
                # Create the output filename. We keep the original filename
                # to maintain the vehicle ID.
                output_path = os.path.join(output_folder, filename)
                
                # Save the processed image
                cv2.imwrite(output_path, processed_image)
                print(f"Processed and saved: {output_path}")

# Example usage of the function
input_directory = "keyframes"
output_directory = "processed_keyframes"

process_all_keyframes(input_directory, output_directory)