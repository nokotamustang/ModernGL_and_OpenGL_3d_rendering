
from PIL import Image
import numpy as np
import argparse

# Simple command line app to convert DX normal map to GL normal map (inverted y-component)
# Despite the naming used, this could be used to convert from GL to DX too


def convert_dx_to_gl_normal_map(input_path, output_path):
    # Load the PNG image
    try:
        in_image = Image.open(input_path)
        if in_image.mode != 'RGB' and in_image.mode != 'RGBA':
            raise ValueError(f"input image must be in RGB or RGBA format, is: {in_image.mode}")
    except Exception as e:
        print(f"error loading image: {e}")
        return

    # Convert image to numpy array
    image_array = np.array(in_image, dtype=np.uint8)

    # Invert the green channel (index 1) for DirectX to OpenGL conversion
    image_array[:, :, 1] = 255 - image_array[:, :, 1]

    # Convert back to PIL image
    if in_image.mode == 'RGB':
        converted_image = Image.fromarray(image_array, mode='RGB')
    elif in_image.mode == 'RGBA':
        converted_image = Image.fromarray(image_array, mode='RGBA')

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
    input_path = "../textures/brick_bump_dx.png"
    output_path = "../textures/brick_bump_gl.png"
    if args.input:
        input_path = args.input
    if args.output:
        output_path = args.output

    # Call conversion function with provided arguments
    convert_dx_to_gl_normal_map(input_path, output_path)


if __name__ == "__main__":
    main()
