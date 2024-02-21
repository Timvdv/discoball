import time
from led.led import Led
from effects.random_color import random_color_effect
from effects.rainbow_effect import rainbow_effect, vertical_rainbow_effect
from effects.audio_effect import AudioEffect
from effects.band_loop import band_loop_with_individual_band_colors
from effects.video_effect import capture_image, process_image, map_image_to_leds2
from effects.youtube_effect import YoutubeEffect
import numpy as np
import picamera
from config import BANDS, NUM_PIXELS
from audio.audio_processor import AudioProcessor
from rpi_ws281x import Color
from threading import Thread, Event
import signal
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from threading import Thread, Event
import signal
import os
from pydantic import BaseModel

class EffectName(BaseModel):
    effect: str

stop_event = Event()

audio_brightness_active = False  # Track if AUDIO_BRIGHTNESS is active

def signal_handler(signum, frame):
    print("Interrupt received, shutting down...")
    stop_event.set()

def signal_handler(signum, frame):
    print("Interrupt received, shutting down...")
    stop_event.set()

signal.signal(signal.SIGINT, signal_handler)

current_effect = 'NONE'

def calculate_brightness(magnitude):
    max_magnitude = 5000  # Maximum magnitude value
    max_brightness = 255  # Maximum brightness value
    return min(int((magnitude / max_magnitude) * max_brightness), 255)

def light_up_all_hexagons(led_strip, hexagon_ranges, color):
    for hexagon_index in hexagon_ranges:
        for led_index in hexagon_ranges[hexagon_index]:
            led_strip.setPixelColor(led_index, color)
    led_strip.show()

def audio_brightness_effect(strip, audio_processor):
    while not stop_event.is_set():
        global audio_brightness_active
        if audio_brightness_active:
            # Capture and process audio
            freqs, magnitudes = audio_processor.process_audio()

            # Calculate brightness based on the max magnitude
            if magnitudes.size > 0:
                max_magnitude = max(magnitudes)
                brightness = calculate_brightness(max_magnitude)
                strip.set_brightness(brightness)

        time.sleep(0.01)  # Sleep briefly to avoid CPU load

def main():
    strip = Led()
    hexagon_ranges = strip.create_hexagon_mappings_for_bands()
    audio_processor = AudioProcessor()
    camera = picamera.PiCamera()
    camera.resolution = (32, 32)
    frame_interval = 1.0 / 30
    time.sleep(2)  # Camera warm-up time

    strip.turn_off_all_lights()

    youtube_effect = YoutubeEffect(strip, (32, 32), './video/test.mp4')
    youtube_effect2 = YoutubeEffect(strip, (32, 32), './video/test1.mp4')
    youtube_effect3 = YoutubeEffect(strip, (32, 32), './video/test222.mp4')
    audio_effect = AudioEffect(strip)

    global audio_brightness_thread

    # Create the audio processing thread
    audio_brightness_thread = Thread(target=audio_brightness_effect, args=(strip, audio_processor))
    audio_brightness_thread.start()

    while not stop_event.is_set():
        global current_effect

        if current_effect == "RANDOM_COLOR":
            random_color_effect(strip, hexagon_ranges, BANDS)
        elif current_effect == "BAND_LOOP_INDIVIDUAL":
            band_loop_with_individual_band_colors(strip, hexagon_ranges, BANDS)
        elif current_effect == "RAINBOW":
            rainbow_effect(strip, hexagon_ranges, BANDS, delay=0.1)
        elif current_effect == "VERTICAL_RAINBOW":
            vertical_rainbow_effect(strip, hexagon_ranges, BANDS)
        elif current_effect == "YOUTUBE":
            youtube_effect.process_frame()
        elif current_effect == "YOUTUBE2":
            youtube_effect2.process_frame()
        elif current_effect == "YOUTUBE3":
            youtube_effect3.process_frame()
        elif current_effect == "AUDIO_REACTIVE":
            # Capture and process audio
            freqs, magnitudes = audio_processor.process_audio()

            # If there's audio data, map it to LEDs
            if freqs.size > 0 and magnitudes.size > 0:
                audio_effect.map_audio_to_leds(freqs, magnitudes, hexagon_ranges)

        elif current_effect == "VIDEO":
            img = capture_image(camera)
            processed_img = process_image(img)
            map_image_to_leds2(processed_img, strip, BANDS, hexagon_ranges)
        elif current_effect == "ALL_HEXAGONS":
            light_up_all_hexagons(strip, hexagon_ranges, Color(255, 0, 255))

        # Use interruptible sleep
        stop_event.wait(timeout=0.01)

def set_effect(effect_name):
    global current_effect
    current_effect = effect_name

app = FastAPI()
templates = Jinja2Templates(directory="web")
stop_event = Event()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/set_effect")
async def change_effect(effect: EffectName):
    set_effect(effect.effect)
    return {"message": f"Effect set to {effect.effect}"}

@app.post("/toggle_audio_brightness")
async def toggle_audio_brightness(request: Request):
    global audio_brightness_active
    audio_brightness_active = not audio_brightness_active  # Toggle the state
    return {"message": f"AUDIO_BRIGHTNESS {'activated' if audio_brightness_active else 'deactivated'}"}

if __name__ == "__main__":
    disco_thread = Thread(target=main)
    disco_thread.start()

    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=5000)
    except KeyboardInterrupt:
        print("Keyboard Interrupt, stopping...")
        stop_event.set()
        disco_thread.join(timeout=10)
        print("Background thread stopped.")
    finally:
        print("Cleaning up and exiting.")
        # Any additional cleanup code here