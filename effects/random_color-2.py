import time
import random
from rpi_ws281x import Color

def random_color_effect(led_strip, hexagon_ranges, bands):
    min_brightness = 100
    max_brightness = 255
    brightness_step = 50
    sleep_duration = 0.1
    max_off_time = 5  # Maximum off time in seconds

    hexagon_colors = {}
    hexagon_off_times = {}  # Store off times for each hexagon
    hexagon_off_start = {}  # Store the start time of the off period

    # Initialize colors for each hexagon and assign random off times
    for hexagon_position in range(9):
        for band_index, band in enumerate(bands):
            if hexagon_position < len(band):
                second_hexagon_dict = band[hexagon_position]
                second_hexagon_index = next(iter(second_hexagon_dict))
                hexagon_colors[second_hexagon_index] = Color(0, 0, 0)  # Initially turned off
                hexagon_off_times[second_hexagon_index] = random.uniform(0, max_off_time)
                hexagon_off_start[second_hexagon_index] = time.time()

    while True:
        for hexagon_index in hexagon_colors.keys():
            current_time = time.time()
            if current_time - hexagon_off_start[hexagon_index] > hexagon_off_times[hexagon_index]:
                # Hexagon turns on and changes color
                color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                hexagon_colors[hexagon_index] = color
                hexagon_off_start[hexagon_index] = current_time  # Reset off start time

                # Apply the color with full brightness
                led_strip.light_up_hexagon(hexagon_ranges, hexagon_index, color, max_brightness)

        led_strip.show()
        time.sleep(sleep_duration)