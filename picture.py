#!/usr/bin/env python3

from pathlib import Path
import replicate
import subprocess
from time import sleep
import datetime

from databases import Database

import board
from picamera import PiCamera

import configparser

# spoken prompts without going back into node red

def curl_speak(phrase):

    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech'''.format(speech = phrase)
    cl_array = cl.split()
    #print(cl_array)
    subprocess.run(cl_array, check=True, capture_output=True).stdout
    return


# coloured LEDS on front of voice bonnet, for primitive feedback
from digitalio import DigitalInOut, Direction, Pull
import adafruit_dotstar

DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6
dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

# not used immediately, but need 'owner' of picture

database = Database("sqlite:///var/spool/mema/db/memories.db")

config = configparser.ConfigParser()
config.read('etc/mema.ini')



camera = PiCamera()
camera.resolution = (1024, 768)

# can't have this a the moment, no screen
# camera.start_preview()
# Camera warm-up time
dots[0] = (255,0,0)  # red

sleep(2)

unix_time = int(datetime.datetime.now().timestamp())
file_path = config['main']['media_directory'] + "pic/" + str(unix_time) + ".jpg" 
#print('taking picture')

phrase = config['en_prompts']['taking_picture'].replace(' ','_')
curl_speak(phrase)

camera.capture(file_path)

dots[0] = (0,255,0)  # red
#print('picture taken')

camera.close()
sleep(2)

model = replicate.models.get("j-min/clip-caption-reward")
image_file = Path(file_path)

# prediction phase
dots[0] = (255,0,0)  # green

phrase = config['en_prompts']['trying_caption'].replace(' ','_')
curl_speak(phrase)
sleep(2)
dots.deinit()

result = model.predict(image=image_file)
print(result  + "|" + file_path)
