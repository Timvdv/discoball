import numpy as np
import sounddevice as sd
import time
import collections
import colorsys
from rpi_ws281x import PixelStrip, Color
import board

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

def map_frequency_to_hue(freqs, magnitudes, current_hue, smoothing_factor=0.1):
    dominant_index = np.argmax(magnitudes)
    dominant_freq = freqs[dominant_index]
    target_hue = (dominant_freq % 1000) / 1000

    # Smooth transition between current hue and target hue
    new_hue = (1 - smoothing_factor) * current_hue + smoothing_factor * target_hue
    return new_hue

def calculate_volume(samples):
    volume = np.mean(np.abs(samples))
    normalized_volume = min(volume / 0.1, 1)  # Normalize volume to a scale of 0 to 1
    return normalized_volume

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

# Main function

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

    strip = setup_neopixel_leds(num_pixels, gpio_pin, freq_hz, dma, invert, brightness, channel)

    while True:
        # Capture audio samples
        duration = 0.01  # Duration of the audio sample in seconds
        sample_rate = 44100
        window_size = int(duration * sample_rate)
        samples = capture_audio_samples(window_size, sample_rate)

        # Compute FFT and get frequency magnitudes
        freqs, magnitudes = compute_fft(samples, sample_rate)

        # Calculate volume
        volume = calculate_volume(samples)

       # Map dominant frequency to hue with smoothing
        current_hue = map_frequency_to_hue(freqs, magnitudes, current_hue)

        # Calculate volume
        volume = calculate_volume(samples)

        # Display color on LEDs based on frequency and volume
        display_color_on_leds(strip, current_hue, volume)

if __name__ == '__main__':
    main()