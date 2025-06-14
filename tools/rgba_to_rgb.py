
from PIL import Image
import numpy as np
import argparse

# Simple command line app to remove the A channel from RGBA

modes = {
    1: "1-bit pixels, black and white, stored with one pixel per byte",
    "L": "8-bit pixels, grayscale",
    "P": "8-bit pixels, mapped to any other mode using a color palette",
    "RGB": "3x8-bit pixels, true color",
    "RGBA": "4x8-bit pixels, true color with transparency mask",
    "CMYK": "4x8-bit pixels, color separation",
    "YCbCr": "3x8-bit pixels, color video format",
    "LAB": "3x8-bit pixels, the L*a*b color space",
    "HSV": "3x8-bit pixels, Hue, Saturation, Value color space",
    "I": "32-bit signed integer pixels",
    "F": "32-bit floating point pixels"
}


def convert_dx_to_gl_normal_map(input_path, output_path):
    try:
        in_image = Image.open(input_path)

        print(f"image        : {in_image.filename}")
        print(f"mode         : {in_image.mode}")
        print(f"as           : {modes[in_image.mode]}")
        print(f"format       : {in_image.format}")
        print(f"size         : {in_image.size}")
        print(f"width        : {in_image.width}")
        print(f"height       : {in_image.height}")
        print(f"bands        : {in_image.getbands()}")
        print(f"palette      : {in_image.palette}")
        print(f"info         : {in_image.info}")
        print(f"transparency : {in_image.has_transparency_data}")

        if output_path == None:
            print("no output file, done")
            return

        if in_image.mode != 'RGBA':
            raise ValueError(f"input image must be in RGBA format, is: {in_image.mode}")
    except Exception as e:
        print(f"error loading image: {e}")
        return

    # Convert image to numpy array
    background = Image.new("RGB", in_image.size, (255, 255, 255))
    background.paste(in_image, mask=in_image.split()[3])  # 3 is the alpha channel
    image_array = np.array(background, dtype=np.uint8)

    # Convert back to PIL image without A channel
    converted_image = Image.fromarray(image_array, mode='RGB')

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
    output_path = None
    if args.input:
        input_path = args.input
    if args.output:
        output_path = args.output

    # Call conversion function with provided arguments
    convert_dx_to_gl_normal_map(input_path, output_path)


if __name__ == "__main__":
    main()
