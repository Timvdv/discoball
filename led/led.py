from rpi_ws281x import PixelStrip, Color
from config import BANDS, DATA_PIN, NUM_PIXELS, FREQ_HZ, DMA, BRIGHTNESS, INVERT, CHANNEL
from time import time
from random import random

class Led:
    def __init__(self):
        self.strip = PixelStrip(NUM_PIXELS, DATA_PIN, FREQ_HZ, DMA, INVERT, BRIGHTNESS, CHANNEL)
        self.strip.begin()

    def setPixelColor(self, led_index, color):
        self.strip.setPixelColor(led_index, color)

    def set_brightness(self, brightness):
        """
        Set the brightness of the LED strip.

        :param brightness: Brightness value (0-255)
        """
        if 0 <= brightness <= 255:
            self.strip.setBrightness(brightness)
        else:
            print("Brightness value should be between 0 and 255")

    def numPixels(self):
        return NUM_PIXELS

    def show(self):
        self.strip.show()

    def light_up_hexagon(self, hexagon_ranges, hexagon_index, color):
        hexagon_range = hexagon_ranges.get(hexagon_index, [])

        for led_index in hexagon_range:
            self.strip.setPixelColor(led_index, color)

    def turn_on_all_lights(self):
        for i in range(NUM_PIXELS):
            self.strip.setPixelColor(i, Color(255, 0, 0))
        self.strip.show()

    def turn_off_all_lights(self):
        for i in range(NUM_PIXELS):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def create_hexagon_mappings_for_bands(self):
        led_mapping = {}
        for band in BANDS:
            for hexagon_dict in band:
                for hexagon_index, (led_count, _) in hexagon_dict.items():
                    start_position = hexagon_index
                    hexagon_range = range(start_position, start_position + led_count)
                    led_mapping[hexagon_index] = hexagon_range
        return led_mapping


def brightness_effect(led_strip, hexagon_ranges, bands):
    min_brightness = 50  # Minimum brightness value (0-255)
    max_brightness = 255 # Maximum brightness value (0-255)
    brightness_step = 20 # Step size for changing brightness
    sleep_duration = 0.05 # Sleep duration for pulsing
    max_delay = 0.5      # Maximum delay before a hexagon starts pulsing

    hexagon_colors = {}
    hexagon_delays = {}

    # Initialize colors and random delays for each hexagon
    for hexagon_position in range(9):
        for band_index, band in enumerate(bands):
            if hexagon_position < len(band):
                second_hexagon_dict = band[hexagon_position]
                second_hexagon_index = next(iter(second_hexagon_dict))
                color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                hexagon_colors[second_hexagon_index] = color
                hexagon_delays[second_hexagon_index] = random.uniform(0, max_delay)

    start_time = time.time()

    # Apply brightness effect with random delays
    for brightness in range(min_brightness, max_brightness, brightness_step) + range(max_brightness, min_brightness, -brightness_step):
        current_time = time.time()
        led_strip.set_brightness(brightness)
        for hexagon_index, color in hexagon_colors.items():
            if current_time - start_time >= hexagon_delays[hexagon_index]:
                led_strip.light_up_hexagon(hexagon_ranges, hexagon_index, color)
        led_strip.show()
        time.sleep(sleep_duration)

