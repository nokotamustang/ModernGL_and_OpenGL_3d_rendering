
from PIL import Image
import numpy as np
import argparse

# Simple command line app to invert a displacement map


def invert_displacement_map(input_path, output_path):
    # Load the PNG image
    try:
        in_image = Image.open(input_path)
        if in_image.mode != 'RGB' and in_image.mode != 'I;16':
            raise ValueError(f"input image must be in RGB or I;16 format, is: {in_image.mode}")
    except Exception as e:
        print(f"error loading image: {e}")
        return

    if in_image.mode == 'RGB':
        image_array = np.array(in_image, dtype=np.uint8)  # Convert image to numpy array
        # Invert the channels (index 1)
        image_array[:, :, 0] = 255 - image_array[:, :, 0]
        image_array[:, :, 1] = 255 - image_array[:, :, 1]
        image_array[:, :, 2] = 255 - image_array[:, :, 2]
        # Convert back to PIL image
        converted_image = Image.fromarray(image_array, mode='RGB')
    elif in_image.mode == 'I;16':
        image_array = np.array(in_image, dtype=np.uint16)  # Convert image to numpy array
        # Invert the channels (index 1)
        image_array[:, :] = 255 - image_array[:, :]
        # Convert back to PIL image
        converted_image = Image.fromarray(image_array, mode='I;16')

    # Save the converted image
    try:
        converted_image.save(output_path, 'PNG')
        print(f"converted image saved to {output_path}")
    except Exception as e:
        print(f"error saving image: {e}")


def main():
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Invert the green channel of a normal map.")
    parser.add_argument("--input", help="Path to the input image.")
    parser.add_argument("--output", help="Path to save the output image.")

    # Parse arguments
    args = parser.parse_args()

    # Default
    input_path = "../textures/brick_wall_disp.png"
    output_path = "../textures/brick_wall_disp.png"
    if args.input:
        input_path = args.input
    if args.output:
        output_path = args.output

    # Call conversion function with provided arguments
    invert_displacement_map(input_path, output_path)


if __name__ == "__main__":
    main()
