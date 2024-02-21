import cv2
import numpy as np
from PIL import Image
from rpi_ws281x import PixelStrip, Color
from config import BANDS, NUM_PIXELS
import time

class YoutubeEffect:
    def __init__(self, strip, matrix_dimensions, video_path):
        self.strip = strip
        self.matrix_dimensions = matrix_dimensions
        self.video_path = video_path
        self.frame_interval = 1.0 / 30  # 30 frames per second
        self.last_frame_time = 0
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print(f"Failed to open video file: {video_path}")

    def process_frame(self):
        current_time = time.time()
        if current_time - self.last_frame_time > self.frame_interval:
            frame = self.capture_video_frame()

            # print(frame)

            if frame is not None:
                processed_img = self.process_video_frame(frame, self.matrix_dimensions)
                self.map_image_to_leds(processed_img)
            else:
                print("Frame capture failed.")

            self.last_frame_time = current_time

    def capture_video_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            return None

    def process_video_frame(self, frame, matrix_dimensions):
        img = Image.fromarray(frame)
        img_resized = img.resize(matrix_dimensions, Image.ANTIALIAS)
        return np.array(img_resized)

    def calculate_average_color(self, img, frame_x, frame_y, count, width, height):
        # Calculate the start and end positions of the region to sample
        x_start = max(0, min(frame_x, width - 1))
        y_start = max(0, min(frame_y, height - 1))
        x_end = min(x_start + count, width)
        y_end = min(y_start + count, height)

        # Ensure the region is within the bounds of the image
        if x_end <= x_start or y_end <= y_start:
            return Color(0, 0, 0)

        # Extract the region and calculate the average color
        region = img[y_start:y_end, x_start:x_end]
        if region.size == 0:
            return (0, 0, 0)

        avg_b, avg_g, avg_r = np.mean(region, axis=(0, 1))
        return (int(avg_r), int(avg_g), int(avg_b))

    def calculate_spherical_coordinates(self, led_position, band_index, bands):
        num_bands = len(bands)
        # Adjust the latitude calculation if bands are not evenly spaced
        latitude = (180.0 / (num_bands - 1)) * band_index - 90

        band = bands[band_index]
        total_leds_in_band = sum(seg[0] for d in band for seg in d.values())

        led_index_in_band = 0
        for d in band:
            for key, (count, _) in d.items():
                if key == led_position:
                    break
                led_index_in_band += count

        # Adjust longitude calculation if bands do not cover full 360 degrees
        longitude = (360.0 / total_leds_in_band) * led_index_in_band

        return latitude, longitude

    def map_spherical_to_frame_coordinates(self, latitude, longitude, frame_width, frame_height):
        # Adjust projection method to fit your specific LED layout
        x = (longitude + 180) * (frame_width / 360)
        y = (90 - latitude) * (frame_height / 180)

        # Ensure coordinates are within the bounds of the video frame
        x = max(0, min(frame_width - 1, x))
        y = max(0, min(frame_height - 1, y))

        return int(x), int(y)

    def interpolate_colors(self, color_start, color_end, num_steps):
        step_r = (color_end[0] - color_start[0]) / num_steps
        step_g = (color_end[1] - color_start[1]) / num_steps
        step_b = (color_end[2] - color_start[2]) / num_steps

        return [(int(color_start[0] + step_r * i), int(color_start[1] + step_g * i), int(color_start[2] + step_b * i)) for i in range(num_steps)]

    def map_image_to_leds(self, processed_img):
        height, width, _ = processed_img.shape

        band_index = 0
        for band in BANDS:
            for led_info in band:
                for start_led, (count, _) in led_info.items():
                    if count > 1:
                        # Calculate start and end positions for color interpolation
                        start_latitude, start_longitude = self.calculate_spherical_coordinates(start_led, band_index, BANDS)
                        end_latitude, end_longitude = self.calculate_spherical_coordinates(start_led + count - 1, band_index, BANDS)

                        start_frame_x, start_frame_y = self.map_spherical_to_frame_coordinates(start_latitude, start_longitude, width, height)
                        end_frame_x, end_frame_y = self.map_spherical_to_frame_coordinates(end_latitude, end_longitude, width, height)

                        start_color = self.calculate_average_color(processed_img, start_frame_x, start_frame_y, 1, width, height)
                        end_color = self.calculate_average_color(processed_img, end_frame_x, end_frame_y, 1, width, height)

                        interpolated_colors = self.interpolate_colors(start_color, end_color, count)

                        for i in range(count):
                            led_index = start_led + i
                            if led_index < NUM_PIXELS:
                                r, g, b = interpolated_colors[i]
                                self.strip.setPixelColor(led_index, Color(r, g, b))
                    else:
                        latitude, longitude = self.calculate_spherical_coordinates(start_led, band_index, BANDS)
                        frame_x, frame_y = self.map_spherical_to_frame_coordinates(latitude, longitude, width, height)
                        color = self.calculate_average_color(processed_img, frame_x, frame_y, 1, width, height)
                        if start_led < NUM_PIXELS:
                            self.strip.setPixelColor(start_led, Color(*color))

            band_index += 1

        self.strip.show()

    def __del__(self):
        if self.cap:
            self.cap.release()