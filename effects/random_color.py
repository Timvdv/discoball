import time
import random
from rpi_ws281x import Color
from config import BANDS, NUM_PIXELS

# Constants for maximum and minimum off and on times in seconds
MAX_OFF_TIME = 5
MIN_OFF_TIME = 1
MAX_ON_TIME = 5
MIN_ON_TIME = 1

# Initialize dictionaries outside the function
hexagon_states = {}
hexagon_off_times = {}
hexagon_off_start = {}
hexagon_brightness = {}
hexagon_colors = {}

def initialize_hexagons(bands):
    for hexagon_position in range(9):
        for band_index, band in enumerate(bands):
            if hexagon_position < len(band):
                hexagon = next(iter(band[hexagon_position]))
                hexagon_states[hexagon] = 'off'
                hexagon_brightness[hexagon] = 0
                hexagon_colors[hexagon] = Color(0, 0, 0)
                hexagon_off_times[hexagon] = random.uniform(MIN_OFF_TIME, MAX_OFF_TIME)
                hexagon_off_start[hexagon] = time.time()

def random_color_effect(led_strip, hexagon_ranges, bands, min_brightness=0, max_brightness=255, brightness_step=15):
    current_time = time.time()

    for hexagon_index in hexagon_states.keys():
        state = hexagon_states[hexagon_index]
        brightness = hexagon_brightness[hexagon_index]

        if state == 'off':
            if current_time - hexagon_off_start[hexagon_index] >= hexagon_off_times[hexagon_index]:
                hexagon_states[hexagon_index] = 'dimming_up'
                hexagon_colors[hexagon_index] = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        elif state == 'dimming_up':
            brightness = min(brightness + brightness_step, max_brightness)
            if brightness == max_brightness:
                hexagon_states[hexagon_index] = 'on'
                hexagon_off_start[hexagon_index] = current_time
        elif state == 'on':
            if current_time - hexagon_off_start[hexagon_index] >= random.uniform(MIN_ON_TIME, MAX_ON_TIME):
                hexagon_states[hexagon_index] = 'dimming_down'
        elif state == 'dimming_down':
            brightness = max(brightness - brightness_step, min_brightness)
            if brightness == min_brightness:
                hexagon_states[hexagon_index] = 'off'
                hexagon_off_start[hexagon_index] = current_time  # Start the off timer
                hexagon_off_times[hexagon_index] = random.uniform(MIN_OFF_TIME, MAX_OFF_TIME)  # Reset off time for next cycle

        hexagon_brightness[hexagon_index] = brightness

        # Apply color and brightness
        color = hexagon_colors[hexagon_index]
        r, g, b = [(color >> 16) & 255, (color >> 8) & 255, color & 255]
        scaled_r = r * brightness // 255
        scaled_g = g * brightness // 255
        scaled_b = b * brightness // 255
        led_strip.light_up_hexagon(hexagon_ranges, hexagon_index, Color(scaled_r, scaled_g, scaled_b))

    led_strip.show()

initialize_hexagons(BANDS)