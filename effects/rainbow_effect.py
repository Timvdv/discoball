import time
import colorsys
from rpi_ws281x import Color

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

def interpolate_color(color1, color2, factor):
    """Interpolate between two RGB colors"""
    return tuple(int(a + (b - a) * factor) for a, b in zip(color1, color2))

def rainbow_effect(strip, hexagon_ranges, bands, delay=0.1, transition_steps=10):
    hue_division = 1.0 / len(bands)

    # Calculate the step factor based on the current time
    current_time = time.time()
    step = int((current_time * 1000) / (delay * 1000)) % transition_steps
    factor = step / float(transition_steps)

    for band_index, band in enumerate(bands):
        current_hue = (band_index * hue_division) % 1.0
        next_hue = ((band_index + 1) % len(bands)) * hue_division
        interpolated_hue = interpolate_hue(current_hue, next_hue, factor)

        current_rgb = colorsys.hsv_to_rgb(current_hue, 1.0, 1.0)
        next_rgb = colorsys.hsv_to_rgb(next_hue, 1.0, 1.0)
        interpolated_rgb = interpolate_color(current_rgb, next_rgb, factor)
        color = Color(int(interpolated_rgb[0] * 255), int(interpolated_rgb[1] * 255), int(interpolated_rgb[2] * 255))

        for hexagon_dict in band:
            hexagon_index = next(iter(hexagon_dict))
            strip.light_up_hexagon(hexagon_ranges, hexagon_index, color)

    strip.show()

def vertical_rainbow_effect(strip, hexagon_ranges, bands, delay=0.1, transition_steps=10):
    max_hexagons_in_band = max(len(band) for band in bands)

    for step in range(transition_steps):
        factor = step / float(transition_steps)

        for hexagon_position in range(max_hexagons_in_band):
            current_hue = (hexagon_position / max_hexagons_in_band) % 1.0
            next_hue = ((hexagon_position + 1) / max_hexagons_in_band) % 1.0
            interpolated_hue = interpolate_hue(current_hue, next_hue, factor)

            rgb = colorsys.hsv_to_rgb(interpolated_hue, 1.0, 1.0)
            color = Color(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

            for band_index, band in enumerate(bands):
                if hexagon_position < len(band):
                    hexagon_dict = band[hexagon_position]
                    hexagon_index = next(iter(hexagon_dict))
                    strip.light_up_hexagon(hexagon_ranges, hexagon_index, color)

        strip.show()
        time.sleep(delay)