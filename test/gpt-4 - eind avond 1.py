import numpy as np
import sounddevice as sd
import time
import collections
import colorsys
from rpi_ws281x import PixelStrip, Color
import board
import math

# Initial setup
DATA_PIN = board.D10
num_pixels = 264
current_hue = 0  # Global variable to store the current hue

def capture_audio_samples(window_size, sample_rate):
    window = collections.deque(maxlen=window_size)

    def audio_callback(indata, frames, time, status):
        window.extend(indata[:, 0])

    with sd.InputStream(samplerate=sample_rate, channels=1, callback=audio_callback):
        while len(window) < window_size:
            time.sleep(0.001)
        return np.array(window)

def compute_fft(samples, sample_rate):
    fft_result = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(len(samples), d=1 / sample_rate)
    return freqs, np.abs(fft_result)

def hue_to_rgb(hue):
    # Convert HSL color to RGB
    r, g, b = colorsys.hls_to_rgb(hue, 0.5, 1)
    return int(r * 255), int(g * 255), int(b * 255)

# Function to setup NeoPixel LEDs
def setup_neopixel_leds(num_pixels, gpio_pin, freq_hz, dma, invert, brightness, channel):
    strip = PixelStrip(num_pixels, gpio_pin, freq_hz, dma, invert, brightness, channel)
    strip.begin()
    return strip

# Function to display color on LEDs based on frequency and volume
def display_color_on_leds(strip, hue, volume):
    r, g, b = hue_to_rgb(hue)
    adjusted_r = int(r * volume)
    adjusted_g = int(g * volume)
    adjusted_b = int(b * volume)

    for i in range(num_pixels):
        strip.setPixelColor(i, Color(adjusted_r, adjusted_g, adjusted_b))
    strip.show()

def calculate_volume(samples, threshold=0.01):
    volume = np.mean(np.abs(samples))
    normalized_volume = volume / 0.1  # Normalize volume to a scale of 0 to 1
    # Apply threshold to handle silence or very low sound levels
    return max(normalized_volume, threshold) if normalized_volume > threshold else 0

def get_logarithmic_index(freq, freqs, num_segments):
    # Map a frequency to its logarithmic position in the spectrum
    min_freq = np.min(freqs)
    max_freq = np.max(freqs)
    freq_ratio = (freq - min_freq) / (max_freq - min_freq)
    log_index = np.log10(1 + 9 * freq_ratio)  # Logarithmic scale
    return min(int(log_index * num_segments), num_segments - 1)

def display_spectrum_on_leds(strip, freqs, magnitudes, num_segments, sensitivity=0.01):
    num_leds_per_segment = math.ceil(num_pixels / num_segments)
    segment_magnitudes = [0] * num_segments

    # Aggregate magnitudes logarithmically into segments
    for freq, magnitude in zip(freqs, magnitudes):
        segment = get_logarithmic_index(freq, freqs, num_segments)
        if segment < num_segments:
            segment_magnitudes[segment] += magnitude

    # Normalize and scale magnitudes for each segment
    max_magnitude = max(segment_magnitudes) if max(segment_magnitudes) > 0 else 1
    normalized_magnitudes = [(mag / max_magnitude) * sensitivity for mag in segment_magnitudes]

    # Update LED colors for each segment
    for i, magnitude in enumerate(normalized_magnitudes):
        r, g, b = hue_to_rgb(i / num_segments)
        adjusted_r = int(r * magnitude * 255)
        adjusted_g = int(g * magnitude * 255)
        adjusted_b = int(b * magnitude * 255)
        for j in range(i * num_leds_per_segment, min((i + 1) * num_leds_per_segment, num_pixels)):
            strip.setPixelColor(j, Color(adjusted_r, adjusted_g, adjusted_b))

    strip.show()

def map_frequency_to_hue(freqs, magnitudes, current_hue, smoothing_factor=0.5):
    # Calculate the weighted average frequency
    weighted_sum = np.sum(freqs * magnitudes)
    total_magnitude = np.sum(magnitudes)
    avg_freq = weighted_sum / total_magnitude if total_magnitude > 0 else 0

    # Map the average frequency to a hue value
    target_hue = (avg_freq % 1000) / 1000

    # Apply a dampening effect for smoother transitions
    new_hue = (1 - smoothing_factor) * current_hue + smoothing_factor * target_hue
    return new_hue


def smooth_magnitudes(magnitudes, window_size=3):
    smoothed = np.convolve(magnitudes, np.ones(window_size)/window_size, mode='same')
    return smoothed

# Main function
def main():
    global current_hue  # use the global current_hue variable
    # LED strip setup
    gpio_pin = 10
    freq_hz = 800000
    dma = 5
    invert = False
    brightness = 255
    channel = 0

    num_segments = 10  # Adjust the number of segments as needed

    strip = setup_neopixel_leds(num_pixels, gpio_pin, freq_hz, dma, invert, brightness, channel)
    while True:
        # Capture audio samples
        duration = 0.01  # Duration of the audio sample in seconds
        sample_rate = 44100
        window_size = int(duration * sample_rate)
        samples = capture_audio_samples(window_size, sample_rate)

        # Compute FFT and get frequency magnitudes
        freqs, magnitudes = compute_fft(samples, sample_rate)

        magnitudes = smooth_magnitudes(magnitudes)

        # Calculate volume with threshold handling
        volume = calculate_volume(samples)

        # Display the frequency spectrum on the LEDs
        display_spectrum_on_leds(strip, freqs, magnitudes, num_segments)

if __name__ == '__main__':
    main()