import time
from PIL import Image, ImageEnhance, ImageOps

import io
import numpy as np
from rpi_ws281x import Color

def map_image_to_leds2(img, strip, bands, hexagon_ranges):
    # Find the maximum number of hexagons in any single band
    max_hexagons_per_band = max(len(band) for band in bands)
    total_hexagons = sum(len(band) for band in bands)

#     # Resize the image to match the number of hexagons
    img = img.resize((total_hexagons, 1), resample=Image.BILINEAR)
    img_array = np.array(img)

    hexagon_index = 0
    for band in bands:
        for hexagon_dict in band:
            # Get the color of the corresponding pixel in the image
            r, g, b = img_array[0, hexagon_index]
            color = Color(int(r), int(g), int(b))

            # Light up the hexagon with this color
            led_index = next(iter(hexagon_dict))
            strip.light_up_hexagon(hexagon_ranges, led_index, color)

            hexagon_index += 1

    # Set specific pixels to black (off)
    black_pixels = [126, 127, 128, 129, 130, 131]
    for pixel in black_pixels:
        strip.setPixelColor(pixel, Color(0,0,0))

    strip.show()
# def map_image_to_leds2(img, strip, bands, hexagon_ranges):
#     # Count total number of hexagons across all bands
#     total_hexagons = sum(len(band) for band in bands)

#     # Resize the image to match the number of hexagons
#     img = img.resize((total_hexagons, 1), resample=Image.BILINEAR)
#     img_array = np.array(img)

#     hexagon_index = 0
#     for band in bands:
#         for hexagon_dict in band:
#             # Get the color of the corresponding pixel in the image
#             r, g, b = img_array[0, hexagon_index]
#             color = Color(int(r), int(g), int(b))

#             # Light up the hexagon with this color
#             led_index = next(iter(hexagon_dict))
#             strip.light_up_hexagon(hexagon_ranges, led_index, color)

#             hexagon_index += 1

#     strip.setPixelColor(126, Color(0,0,0))
#     strip.setPixelColor(127, Color(0,0,0))
#     strip.setPixelColor(128, Color(0,0,0))
#     strip.setPixelColor(129, Color(0,0,0))
#     strip.setPixelColor(130, Color(0,0,0))
#     strip.setPixelColor(131, Color(0,0,0))

#     strip.show()

# def map_image_to_leds(img, strip):
#     img = img.resize((strip.numPixels(), 1), resample=Image.BILINEAR)
#     img_array = np.array(img)

#     for i in range(strip.numPixels()):
#         r, g, b = img_array[0, i]
#         color = Color(int(r), int(g), int(b))  # Correctly create the color
#         strip.setPixelColor(i, color)

#     strip.setPixelColor(132, Color(255,0,255))
#     strip.setPixelColor(133, Color(255,0,255))
#     strip.setPixelColor(134, Color(255,0,255))
#     strip.setPixelColor(135, Color(255,0,255))
#     strip.setPixelColor(136, Color(255,0,255))
#     strip.setPixelColor(137, Color(255,0,255))

#     strip.show()

def capture_image(camera):
    with io.BytesIO() as stream:
        camera.capture(stream, format='jpeg', use_video_port=True)
        stream.seek(0)
        return Image.open(stream).convert('RGB')

def process_image(img, saturation_factor=2.0, rotation_speed=10.0, elapsed_time=0):
    # Mirror the image left to right
    img_mirrored = ImageOps.mirror(img)

    # Enhance the color saturation
    enhancer = ImageEnhance.Color(img_mirrored)
    img_saturated = enhancer.enhance(saturation_factor)

    # Rotate the image
    img_rotated = img_saturated.rotate((elapsed_time * rotation_speed) % 360, resample=Image.BICUBIC, expand=False)

    return img_rotated