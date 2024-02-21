import time
from rpi_ws281x import PixelStrip, Color
import random
import colorsys

# Configuration:
DATA_PIN = 10  # GPIO pin number connected to the pixels
NUM_PIXELS = 264  # Number of LED pixels
FREQ_HZ = 800000  # LED signal frequency in hertz
DMA = 10  # DMA channel to use for generating signal
BRIGHTNESS = 10  # Set to 0 for darkest and 255 for brightest
INVERT = False  # True to invert the signal
CHANNEL = 0  # Set to '1' for specific GPIOs

# Bands configuration
bands = [
    [
        {126: (6, 1)},
        {126: (6, 1)},
        {126: (6, 1)},
        {126: (6, 1)},
        {126: (6, 1)},
        {126: (6, 1)},
        {126: (6, 1)},
        {126: (6, 1)},
        {126: (6, 1)},
    ],
    [
        {78: (6, 1)},
        {78: (6, 1)},
        {84: (10, 1)},
        {94: (6, 1)},
        {94: (6, 1)},
        {100: (10, 1)},
        {110: (6, 1)},
        {110: (6, 1)},
        {116: (10, 1)},
    ],
    [
        {0: (10, 1)},
        {68: (10, 1)},
        {62: (6, 1)},
        {52: (10, 1)},
        {42: (10, 1)},
        {36: (6, 1)},
        {26: (10, 1)},
        {16: (10, 1)},
        {10: (6, 1)},
    ],
    [
        {206: (6, 1)},
        {196: (10, 1)},
        {186: (10, 1)},
        {258: (6, 1)},
        {248: (10, 1)},
        {238: (10, 1)},
        {232: (6, 1)},
        {222: (10, 1)},
        {212: (10, 1)},
    ],
    [
        {144: (10, 1)},
        {138: (6, 1)},
        {138: (6, 1)},
        {176: (10, 1)},
        {166: (6, 1)},
        {166: (6, 1)},
        {160: (10, 1)},
        {154: (6, 1)},
        {154: (6, 1)},
    ],
    [
        {132: (6, 1)},
        {132: (6, 1)},
        {132: (6, 1)},
        {132: (6, 1)},
        {132: (6, 1)},
        {132: (6, 1)},
        {132: (6, 1)},
        {132: (6, 1)},
        {132: (6, 1)},
    ],
]

def setup_neopixel_leds(num_pixels):
    strip = PixelStrip(num_pixels, DATA_PIN, FREQ_HZ, DMA, INVERT, BRIGHTNESS, CHANNEL)
    strip.begin()
    return strip

# Function to light up a specific hexagon
def light_up_hexagon(strip, hexagon_ranges, hexagon_index, color):
    hexagon_range = hexagon_ranges.get(hexagon_index, [])

    print(hexagon_range)

    for led_index in hexagon_range:
        strip.setPixelColor(led_index, color)
    strip.show()

# Function to light up all hexagons in a band with a specific color
def light_up_band(strip, hexagon_ranges, band_index, color):
    band = bands[band_index]
    for hexagon_dict in band:
        hexagon_index = next(iter(hexagon_dict))
        light_up_hexagon(strip, hexagon_ranges, hexagon_index, color)

def turn_off_all_lights(strip, num_pixels):
    for i in range(num_pixels):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def turn_on_all_lights(strip, num_pixels):
    for i in range(num_pixels):
        strip.setPixelColor(i, Color(255, 0, 0))
    strip.show()

def random_color_effect(strip, hexagon_ranges, bands, iterations=10):
    for _ in range(iterations):
        for hexagon_position in range(9):
            for band_index, band in enumerate(bands):
                if hexagon_position < len(band):  # Check if the hexagon exists in the band
                    second_hexagon_dict = band[hexagon_position]
                    second_hexagon_index = next(iter(second_hexagon_dict))
                    # Generate a random color
                    random_color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    light_up_hexagon(strip, hexagon_ranges, second_hexagon_index, random_color)
                    turn_off_all_lights(strip, NUM_PIXELS)
            time.sleep(0.1)


def shift_colors_down(bands_colors):
    return [bands_colors[-1]] + bands_colors[:-1]

def interpolate_hue(hue1, hue2, factor):
    """Interpolate between two hues"""
    # Ensure the hue interpolation wraps around the color wheel
    diff = hue2 - hue1
    if diff > 0.5:
        diff -= 1.0
    elif diff < -0.5:
        diff += 1.0
    return (hue1 + diff * factor) % 1.0

def rainbow_effect(strip, hexagon_ranges, bands, delay=0.1, transition_steps=3):
    hue_division = 1.0 / len(bands)
    iteration = 0

    while True:
        for step in range(transition_steps):
            factor = step / float(transition_steps)

            for band_index, band in enumerate(bands):
                current_hue = ((band_index + iteration) % len(bands)) * hue_division
                next_hue = ((band_index + iteration + 1) % len(bands)) * hue_division
                interpolated_hue = interpolate_hue(current_hue, next_hue, factor)

                rgb = colorsys.hsv_to_rgb(interpolated_hue, 1.0, 1.0)
                color = Color(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

                for hexagon_dict in band:
                    hexagon_index = next(iter(hexagon_dict))
                    light_up_hexagon(strip, hexagon_ranges, hexagon_index, color)

            time.sleep(delay)

        iteration += 1

def vertical_rainbow_effect(strip, hexagon_ranges, bands, delay=0.1, transition_steps=3):
    max_hexagons_in_band = max(len(band) for band in bands)
    iteration = 0

    while True:
        for step in range(transition_steps):
            factor = step / float(transition_steps)

            for hexagon_position in range(max_hexagons_in_band):
                current_hue = ((hexagon_position + iteration) % max_hexagons_in_band) / max_hexagons_in_band
                next_hue = ((hexagon_position + iteration + 1) % max_hexagons_in_band) / max_hexagons_in_band
                interpolated_hue = interpolate_hue(current_hue, next_hue, factor)

                rgb = colorsys.hsv_to_rgb(interpolated_hue, 1.0, 1.0)
                color = Color(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

                for band_index, band in enumerate(bands):
                    if hexagon_position < len(band):
                        hexagon_dict = band[hexagon_position]
                        hexagon_index = next(iter(hexagon_dict))
                        light_up_hexagon(strip, hexagon_ranges, hexagon_index, color)

            time.sleep(delay)

        iteration += 1

def main():
    strip = setup_neopixel_leds(NUM_PIXELS)
    hexagon_ranges = create_hexagon_mappings_for_bands(bands)

    turn_off_all_lights(strip, NUM_PIXELS)

    while True:
        # random_color_effect(strip, hexagon_ranges, bands, iterations=10)
        # rainbow_effect(strip, hexagon_ranges, bands, delay=0.1)
        vertical_rainbow_effect(strip, hexagon_ranges, bands, delay=0.1)

if __name__ == "__main__":
    main()
