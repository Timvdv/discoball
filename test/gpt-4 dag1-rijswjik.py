import numpy as np
import sounddevice as sd
import io
import time
import picamera
import board
import ctypes
import collections
import random
from rpi_ws281x import PixelStrip
from PIL import Image, ImageEnhance

# Initial setup
DATA_PIN = board.D10
image_width, image_height = 64, 64

# Dynamic audio adjustment class
class DynamicAudioAdjustment:
    def __init__(self, window_size, sensitivity_scale=3.0, min_sensitivity=1, max_sensitivity=5):
        self.window_size = window_size
        self.sensitivity_scale = sensitivity_scale
        self.min_sensitivity = min_sensitivity
        self.max_sensitivity = max_sensitivity
        self.recent_levels = collections.deque(maxlen=window_size)

    def update_level(self, level):
        self.recent_levels.append(level)

    def compute_sensitivity(self):
        if not self.recent_levels:
            return self.min_sensitivity
        avg_level = sum(self.recent_levels) / len(self.recent_levels)
        dynamic_sensitivity = self.sensitivity_scale / max(avg_level, 0.01)
        return min(max(self.min_sensitivity, dynamic_sensitivity), self.max_sensitivity)

# Function to compute audio intensities with dynamic sensitivity
def compute_audio_intensities(fft_magnitudes, num_leds, led_data, dynamic_adjustment, focus_on_bass=True, intensity_scale=2.0):
    num_bins = len(fft_magnitudes)
    if focus_on_bass:
        weighting_function = np.linspace(1, 0, num_bins)
        fft_magnitudes = fft_magnitudes * weighting_function
    avg_magnitude = np.mean(fft_magnitudes)
    dynamic_adjustment.update_level(avg_magnitude)
    dynamic_sensitivity = dynamic_adjustment.compute_sensitivity()
    audio_intensity = min(1, avg_magnitude / dynamic_sensitivity) * intensity_scale
    audio_intensities = [audio_intensity] * len(led_data)
    return audio_intensities

def combine_audio_and_video_effects(led_data, audio_intensities):
    combined_led_data = []
    avg_audio_intensity = np.mean(audio_intensities)

    for color in led_data:
        r = min(255, int(((color >> 16) & 255) * avg_audio_intensity))
        g = min(255, int(((color >> 8) & 255) * avg_audio_intensity))
        b = min(255, int((color & 255) * avg_audio_intensity))

        combined_color = (r << 16) | (g << 8) | b
        combined_led_data.append(combined_color)

    return combined_led_data

def capture_audio_samples(window_size, sample_rate):
    window = collections.deque(maxlen=window_size)

    def audio_callback(indata, frames, time, status):
        window.extend(indata[:, 0])

    with sd.InputStream(samplerate=sample_rate, channels=1, callback=audio_callback):
        while len(window) < window_size:
            time.sleep(0.001)
        return np.array(window)

def compute_fft(samples, sample_rate=44100):
    fft_result = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(len(samples), d=1 / sample_rate)
    return freqs, np.abs(fft_result)

def rotate_image_around_center(img, angle):
    img_center = tuple(np.array(img.size) // 2)
    img_rotated = img.rotate(angle, resample=Image.BICUBIC, center=img_center)
    return img_rotated

def increase_saturation(img, saturation_factor):
    enhancer = ImageEnhance.Color(img)
    img_saturated = enhancer.enhance(saturation_factor)
    return img_saturated

def generate_disco_ball_mapping(image_width, image_height, num_large_hexagons=20, large_hexagon_leds=10, num_small_hexagons=12, small_hexagon_leds=6):
    large_hexagon_step = image_width // num_large_hexagons
    small_hexagon_step = image_width // num_small_hexagons

    ball_mapping = []

    # Generate mapping for large hexagons
    for i in range(num_large_hexagons):
        for j in range(large_hexagon_leds):
            x = i * large_hexagon_step + (j * large_hexagon_step) // large_hexagon_leds
            y = image_height // 2
            ball_mapping.append((x, y))

    # Generate mapping for small hexagons
    for i in range(num_small_hexagons):
        for j in range(small_hexagon_leds):
            x = i * small_hexagon_step + (j * small_hexagon_step) // small_hexagon_leds
            y = (image_height // 4) if i % 2 == 0 else (3 * image_height // 4)
            ball_mapping.append((x, y))

    return ball_mapping


def capture_image(resolution=(64, 64)):
    with picamera.PiCamera() as camera:
        camera.resolution = resolution
        time.sleep(2)  # Camera warm-up time
        with io.BytesIO() as stream:
            camera.capture(stream, format='jpeg')
            stream.seek(0)
            img = Image.open(stream).convert('RGB')
            img = img.copy()  # Create a separate copy of the image to avoid I/O issues
    return img

def map_image_to_ball(img, ball_mapping):
    led_data = []
    img_array = np.array(img)
    for i, coord in enumerate(ball_mapping):
        x, y = coord
        r, g, b = img_array[y, x]
        color = (r << 16) | (g << 8) | b
        led_data.append(ctypes.c_uint32(color).value)
    return led_data

def capture_video_frame(camera, saturation_factor=2.0, rotation_speed=10.0):
    start_time = time.time()
    with io.BytesIO() as stream:
        camera.capture(stream, format='jpeg', use_video_port=True)
        stream.seek(0)
        img = Image.open(stream).convert('RGB')
        img = img.copy()  # Create a separate copy of the image to avoid I/O issues
        img = increase_saturation(img, saturation_factor)  # Increase the saturation of the image

        # Rotate the image around its center based on elapsed time
        elapsed_time = time.time() - start_time
        rotation_angle = (elapsed_time * rotation_speed) % 360
        img = rotate_image_around_center(img, rotation_angle)

    return img

# Function to setup NeoPixel LEDs
def setup_neopixel_leds(num_pixels, gpio_pin, freq_hz, dma, invert, brightness, channel):
    strip = PixelStrip(num_pixels, gpio_pin, freq_hz, dma, invert, brightness, channel)
    strip.begin()
    return strip

# Function to display image on LEDs
def display_image_on_leds(strip, led_data):
    for i, color in enumerate(led_data):
        strip.setPixelColor(i, color)
    strip.show()

# Main function
# Main function
def main():
    # Define LED ball parameters
    num_pixels = 264
    gpio_pin = 10  # GPIO pin connected to the pixels (must support PWM)
    freq_hz = 800000  # LED signal frequency in Hz (usually 800kHz)
    dma = 5  # DMA channel to use for generating signal (try 5)
    invert = False  # True to invert the signal (when using NPN transistor level shift)
    brightness = 255  # Set to 0 for darkest and 255 for brightest
    channel = 0  # PWM channel

    # Set up the LED strip
    strip = setup_neopixel_leds(num_pixels, gpio_pin, freq_hz, dma, invert, brightness, channel)

    # Initialize the dynamic adjustment system
    dynamic_adjustment = DynamicAudioAdjustment(window_size=10, sensitivity_scale=2.0)

    # Generate the ball_mapping variable
    ball_mapping = generate_disco_ball_mapping(image_width, image_height)

    # Main loop to capture video frames and update the LED strip
    with picamera.PiCamera() as camera:
        camera.resolution = (image_width, image_height)
        camera.framerate = 30
        time.sleep(2)  # Camera warm-up time

        while True:
            # Capture video frame
            img = capture_video_frame(camera)
            led_data = map_image_to_ball(img, ball_mapping)

            # Capture audio samples
            duration = 0.01  # Duration of the audio sample in seconds
            sample_rate = 44100
            window_size = int(duration * sample_rate)
            samples = capture_audio_samples(window_size, sample_rate)

            # Compute the FFT of the audio samples
            freqs, magnitudes = compute_fft(samples)

            # Compute audio intensities with dynamic sensitivity
            audio_intensities = compute_audio_intensities(magnitudes, num_pixels, led_data, dynamic_adjustment)

            # Combine audio and video effects
            combined_led_data = combine_audio_and_video_effects(led_data, audio_intensities)

            # Display the combined LED data on the strip
            display_image_on_leds(strip, combined_led_data)

if __name__ == '__main__':
    main()
