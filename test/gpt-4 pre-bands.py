import time
from rpi_ws281x import PixelStrip, Color

# Configuration:
DATA_PIN = 10  # GPIO pin number connected to the pixels
NUM_PIXELS = 264  # Number of LED pixels
FREQ_HZ = 800000  # LED signal frequency in hertz
DMA = 10  # DMA channel to use for generating signal
BRIGHTNESS = 10  # Set to 0 for darkest and 255 for brightest
INVERT = False  # True to invert the signal
CHANNEL = 0  # Set to '1' for specific GPIOs


bands = [
    [{15: (6, 1)}],
    [
        {9: (6, 1)},
        {10: (10, 1)},
        {11: (6, 1)},
        {12: (10, 1)},
        {13: (6, 1)},
        {14: (10, 1)},
    ],
    [
        {0: (10, 1)},
        {1: (6, 1)},
        {2: (10, 1)},
        {3: (10, 1)},
        {4: (6, 1)},
        {5: (10, 1)},
        {6: (10, 1)},
        {7: (6, 1)},
        {8: (10, 1)},
    ],
]

hexagon_leds = [
    (10, 1),
    (6, 1),
    (10, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (6, 1),
    # bottom side
    (6, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (10, 1),
    (6, 1),
    (10, 1),
    (10, 1),
    (6, 1),
    (10, 1),
]


hexagon_leds[0]


# Function to setup NeoPixel LEDs
def setup_neopixel_leds(num_pixels):
    strip = PixelStrip(num_pixels, DATA_PIN, FREQ_HZ, DMA, INVERT, BRIGHTNESS, CHANNEL)
    strip.begin()
    return strip


# Function to light up a specific hexagon
def light_up_hexagon(strip, hexagon_ranges, hexagon_index, color):
    for led_index in hexagon_ranges[hexagon_index]:
        strip.setPixelColor(led_index, color)
    strip.show()


# Function to create hexagon LED mappings
def create_hexagon_mappings(hexagon_leds):
    led_mapping = []
    current_led = 0
    for hexagon_size, count in hexagon_leds:
        for _ in range(count):
            hexagon_range = range(current_led, current_led + hexagon_size)
            led_mapping.append(hexagon_range)
            current_led += hexagon_size
    return led_mapping


# Main function
def main():
    strip = setup_neopixel_leds(NUM_PIXELS)
    hexagon_ranges = create_hexagon_mappings(hexagon_leds)

    while True:
        for i in range(len(hexagon_ranges)):
            light_up_hexagon(strip, hexagon_ranges, i, Color(255, 0, 0))  # Red color
            time.sleep(0.1)  # Wait for 1 second
            light_up_hexagon(strip, hexagon_ranges, i, Color(0, 0, 0))  # Turn off


if __name__ == "__main__":
    main()
