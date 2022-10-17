#!/usr/bin/env python3

import time
import board
import subprocess
import requests
import datetime
from pathlib import Path
import threading

import replicate

from digitalio import DigitalInOut, Direction, Pull

# coloured LEDS on front of voice bonnet, for primitive feedback
import adafruit_dotstar
DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6


'''
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

def counter(name):
    dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

    dots[0] = (255,0,0) # green
    count = 60
    while count > 0:
        #dots.deinit()
        time.sleep(10)
        print(count)
        count -= count
        if count <= 20:
            dots[0] = (0,0,255)
        if count <= 10:
            dots[0] = (0,0,255)
    dots.deinit()
    return
'''


button = DigitalInOut(board.D17)
button.direction = Direction.INPUT
button.pull = Pull.UP

dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

#subprocess.run(["docker stop 9a16d851c7c8", "", "/dev/null"], check=True, capture_output=True, text=True).stdout
try:
    subprocess.run(["docker", "stop", "e63d3b9351a2"], check=True, capture_output=True, text=True).stdout
except subprocess.CalledProcessError as e:
    raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

# make a file name from the current unix timestamp
unix_time = int(datetime.datetime.now().timestamp())
file_path = "/var/spool/mema/rec/" + str(unix_time) + ".wav" 

time.sleep(1)

dots[0] = (255,0,0)  # green

try:
    #print('here')
    subprocess.run(["arecord", "-f", "cd", "-c", "2", "-D", "plug:dsnooped",  "--duration", "60" , file_path], check=True, capture_output=True, text=True).stdout
except subprocess.CalledProcessError as e:
    raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

dots[0] = (0,0,255)  # red

try:
    subprocess.run(["docker", "start", "e63d3b9351a2"], check=True, capture_output=True, text=True).stdout
except subprocess.CalledProcessError as e:
    raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))


# select speech to text model
model = replicate.models.get("openai/whisper")
# format file as path object (openai needs this)
audio_file = Path(file_path)

# give a little feedback
dots[0] = (0,255,0)  # blue

# speech to text on remote server
result = model.predict(audio=audio_file)

# done, feedback 
dots[0] = (255,0,0)  # green
sleep(5)
dots.deinit()

# return result and file path to intent server
print(result['transcription']  + "|" + file_path)
