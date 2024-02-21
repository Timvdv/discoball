import numpy as np
import sounddevice as sd
import time
from scipy.signal import windows

class AudioProcessor:
    def __init__(self, sample_rate=44100, duration=0.05):
        self.sample_rate = sample_rate
        self.duration = duration

    def capture_audio_samples(self):
        """Capture audio samples for a specified duration."""
        samples = []
        def audio_callback(indata, frames, time, status):
            samples.extend(indata[:, 0])

        with sd.InputStream(callback=audio_callback, channels=1, samplerate=self.sample_rate):
            time.sleep(self.duration)
            return np.array(samples)

    def compute_fft(self, samples):
        """Compute the FFT of the audio samples."""
        if len(samples) == 0:
            return np.array([]), np.array([])

        # Apply a window function to the samples
        windowed_samples = samples * windows.hann(len(samples))

        fft_result = np.fft.rfft(windowed_samples)
        freqs = np.fft.rfftfreq(len(samples), d=1 / self.sample_rate)
        return freqs, np.abs(fft_result)

    def process_audio(self):
        samples = self.capture_audio_samples()
        if len(samples) == 0:
            return np.array([]), np.array([])

        # Start with a small amplification factor
        amplified_samples = samples * 2000  # Adjust this factor gradually

        freqs, magnitudes = self.compute_fft(amplified_samples)

        # Debugging print statements
        # print("Max magnitude:", np.max(magnitudes))
        # print("Dominant frequency:", freqs[np.argmax(magnitudes)])

        return freqs, magnitudes