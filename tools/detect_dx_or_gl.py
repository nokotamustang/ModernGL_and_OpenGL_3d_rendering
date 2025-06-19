from PIL import Image
import numpy as np
from skimage import img_as_float
import sys
import argparse


def detect_normal_map_format(image_path):
    try:
        # Load the image using PIL
        img = Image.open(image_path)

        # Convert to RGB if not already
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Convert to NumPy array
        img_array = np.array(img)

        # Convert to float for processing
        img_float = img_as_float(img_array)

        # Extract the green channel (Y component in normal maps)
        green_channel = img_float[:, :, 1]

        # Calculate the mean of the green channel
        green_mean = np.mean(green_channel)

        # DirectX normal maps typically have green channel values biased towards 0 (darker)
        # OpenGL normal maps typically have green channel values biased towards 1 (brighter)
        # This is a heuristic based on the Y-axis direction
        threshold = 0.5  # Midpoint for heuristic
        if green_mean < threshold:
            return "DirectX (DX)"
        else:
            return "OpenGL (GL)"

    except Exception as e:
        return f"Error processing image: {str(e)}"


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Detect if a normal map is in DirectX or OpenGL format.")
    parser.add_argument("--input", help="Path to the normal map image")
    args = parser.parse_args()

    # Detect format
    result = detect_normal_map_format(args.input)
    print(f"Normal map format: {result}")


if __name__ == "__main__":
    main()
