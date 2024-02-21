from rpi_ws281x import Color
import numpy as np
from config import NUM_PIXELS, BANDS
import colorsys

def audio_reactive_effect(led_strip, freqs, magnitudes, max_brightness=255, magnitude_scale=5000):
    if magnitudes.size == 0:
        return  # No magnitudes to process

    # Calculate the average magnitude and apply a scaling factor
    avg_magnitude = np.mean(magnitudes) * magnitude_scale
    # Scale the average magnitude to a brightness value
    brightness = int(avg_magnitude * max_brightness / magnitude_scale)
    brightness = max(0, min(max_brightness, brightness))  # Ensure brightness is within 0-255

    led_strip.set_brightness(brightness)

    # Find the index of the maximum magnitude
    max_magnitude_index = np.argmax(magnitudes)
    # Find the frequency corresponding to the maximum magnitude
    dominant_freq = freqs[max_magnitude_index]

    color = frequency_to_color(dominant_freq)

    for i in range(NUM_PIXELS):
        led_strip.setPixelColor(i, color)

    led_strip.show()

def audio_reactive_effect2(led_strip, freqs, magnitudes, max_brightness=255, magnitude_scale=5000):
    if magnitudes.size == 0:
        return  # No magnitudes to process

    # Calculate the average magnitude and apply a scaling factor
    avg_magnitude = np.mean(magnitudes) * magnitude_scale
    # Scale the average magnitude to a brightness value
    overall_brightness = int(avg_magnitude * max_brightness / magnitude_scale)
    overall_brightness = max(0, min(max_brightness, overall_brightness))

    # Find the index of the maximum magnitude
    max_magnitude_index = np.argmax(magnitudes)
    # Find the frequency corresponding to the maximum magnitude
    dominant_freq = freqs[max_magnitude_index]

    # Reset all pixels to off
    for i in range(NUM_PIXELS):
        led_strip.setPixelColor(i, Color(0, 0, 0))

    # Iterate over BANDS and set colors for specified LEDs
    for band in BANDS:
        for led_info in band:
            for start_led, (count, intensity_factor) in led_info.items():
                color = frequency_to_hue_color(dominant_freq, start_led, NUM_PIXELS, freqs)
                adjusted_color = apply_intensity(color, intensity_factor * overall_brightness)
                for i in range(start_led, start_led + count):
                    if i < NUM_PIXELS:
                        led_strip.setPixelColor(i, adjusted_color)

    led_strip.show()

def frequency_to_color(freq):
    """Map frequency value to a color."""
    if freq < 150:  # Bass
        return Color(255, 0, 0)
    elif freq < 300:  # Mid-range
        return Color(0, 255, 0)
    else:  # Highs
        return Color(0, 0, 255)

def frequency_to_color_gradient(freq, position, total_pixels):
    """Map frequency value to a color with gradient effect."""
    # Adjust these ranges and colors as needed
    if freq < 150:  # Bass
        red = int(255 * position / total_pixels)
        return Color(red, 0, 0)
    elif freq < 300:  # Mid-range
        green = int(255 * position / total_pixels)
        return Color(0, green, 0)
    else:  # Highs
        blue = int(255 * position / total_pixels)
        return Color(0, 0, blue)

def frequency_to_hue_color(freq, position, total_pixels, freqs):
    max_freq = max(freqs) if freqs.size > 0 else 1
    hue = (freq / max_freq) * (position / total_pixels)
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return Color(int(r * 255), int(g * 255), int(b * 255))

def apply_intensity(color, intensity):
    red = (color >> 16) & 0xff
    green = (color >> 8) & 0xff
    blue = color & 0xff

    red = int(red * intensity)
    green = int(green * intensity)
    blue = int(blue * intensity)

    return Color(red, green, blue)