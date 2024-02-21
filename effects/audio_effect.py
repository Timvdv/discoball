import numpy as np
import sounddevice as sd
from scipy.signal import windows
from rpi_ws281x import PixelStrip, Color
from config import BANDS, NUM_PIXELS
import time

class AudioEffect:
    def __init__(self, strip, sample_rate=44100, duration=0.05):
        self.strip = strip
        self.sample_rate = sample_rate
        self.duration = duration

    @staticmethod
    def frequency_to_color(frequency, magnitude):
        # Fixed maximum magnitude for scaling
        max_magnitude = 2000

        # Normalize the magnitude
        brightness = max(0, min(1, magnitude / max_magnitude))

        # Map the frequency to a color
        if frequency < 300:  # Low frequencies - Red
            color = (255, 0, 0)
        elif frequency < 2000:  # Mid frequencies - Green
            color = (0, 255, 0)
        else:  # High frequencies - Blue
            color = (0, 0, 255)

        # Adjust the color brightness
        brightened_color = tuple(int(c * brightness) for c in color)
        return Color(*brightened_color)

    def map_audio_to_leds(self, freqs, magnitudes, hexagon_ranges):
        band_magnitudes = np.array_split(magnitudes, len(BANDS))
        band_frequencies = np.array_split(freqs, len(BANDS))

        for band_index, band in enumerate(BANDS):



            dominant_index = np.argmax(band_magnitudes[band_index])
            dominant_frequency = band_frequencies[band_index][dominant_index]
            dominant_magnitude = band_magnitudes[band_index][dominant_index]

            # Corrected call to frequency_to_color
            color = AudioEffect.frequency_to_color(dominant_frequency, dominant_magnitude)

            for hexagon_dict in band:
                led_index = next(iter(hexagon_dict))
                self.strip.light_up_hexagon(hexagon_ranges, led_index, color)

        self.strip.show()

    def capture_audio_samples(self):
        samples = []
        def audio_callback(indata, frames, time, status):
            samples.extend(indata[:, 0])

        with sd.InputStream(callback=audio_callback, channels=1, samplerate=self.sample_rate):
            time.sleep(self.duration)
            return np.array(samples)

    def compute_fft(self, samples):
        if len(samples) == 0:
            return np.array([]), np.array([])

        windowed_samples = samples * windows.hann(len(samples))
        fft_result = np.fft.rfft(windowed_samples)
        freqs = np.fft.rfftfreq(len(samples), d=1 / self.sample_rate)
        return freqs, np.abs(fft_result)

    def calculate_spherical_coordinates(self, led_position, band_index):
        latitude = (180.0 / (len(BANDS) - 1)) * band_index - 90
        total_leds_in_band = sum(count for _, (count, _) in BANDS[band_index].items())
        longitude = (360.0 / total_leds_in_band) * led_position
        return latitude, longitude
