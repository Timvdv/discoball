import time
import random
from rpi_ws281x import Color
from config import BANDS, NUM_PIXELS

def color_distance(color1, color2):
    """Calculate the distance between two colors in RGB space."""
    r1, g1, b1 = [(color1 >> 16) & 255, (color1 >> 8) & 255, color1 & 255]
    r2, g2, b2 = [(color2 >> 16) & 255, (color2 >> 8) & 255, color2 & 255]
    return ((r2 - r1)**2 + (g2 - g1)**2 + (b2 - b1)**2)**0.5

def generate_random_color(previous_color=None, min_distance=50):
    """Generate a random color that is significantly different from the previous color."""
    while True:
        new_color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        if previous_color is None or color_distance(new_color, previous_color) >= min_distance:
            return new_color

# Global variables
current_index = 0

current_color = generate_random_color()
next_color = generate_random_color(current_color)

color_transition_steps = 10  # Number of steps to transition between colors
color_step = 0
last_update_time = time.time()
update_interval = 0.1

def interpolate_color(color1, color2, factor):
    """Interpolate between two RGB colors."""
    r1, g1, b1 = [(color1 >> 16) & 255, (color1 >> 8) & 255, color1 & 255]
    r2, g2, b2 = [(color2 >> 16) & 255, (color2 >> 8) & 255, color2 & 255]

    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)

    return Color(r, g, b)

def band_loop(led_strip, hexagon_ranges, bands):
    global current_index, current_color, next_color, color_step, last_update_time

    current_time = time.time()

    if current_time - last_update_time >= update_interval:
        # Light up the current hexagon index in all bands
        for band in bands:
            if current_index < len(band):
                hexagon_dict = band[current_index]
                hexagon_index = next(iter(hexagon_dict))
                led_strip.light_up_hexagon(hexagon_ranges, hexagon_index, current_color)

        led_strip.show()
        current_index = (current_index + 1) % 9

        if color_step < color_transition_steps:
            factor = color_step / float(color_transition_steps)
            current_color = interpolate_color(current_color, next_color, factor)
            color_step += 1
        else:
            current_color = next_color
            next_color = generate_random_color(current_color)
            color_step = 0

        last_update_time = current_time

def band_loop_with_individual_band_colors(led_strip, hexagon_ranges, bands):
    global current_index, last_update_time

    # Generate a random color for the current band
    band_color = generate_random_color()

    current_time = time.time()

    if current_time - last_update_time >= update_interval:
        for band_index, band in enumerate(bands):
            if current_index < len(band):
                hexagon_dict = band[current_index]
                hexagon_index = next(iter(hexagon_dict))
                led_strip.light_up_hexagon(hexagon_ranges, hexagon_index, band_color)

        time.sleep(0.1)
        led_strip.show()

        # Check if we are moving to the next band
        next_index = (current_index + 1) % 9
        if next_index < current_index:
            # We are moving to the next band, generate a new color
            band_color = generate_random_color()

        # Update the current index
        current_index = next_index
        last_update_time = current_time