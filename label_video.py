#!/usr/bin/env python3

import os
import sys

from time import sleep
import board
import subprocess
import requests
import datetime
from pathlib import Path

import replicate

import configparser

from digitalio import DigitalInOut, Direction, Pull

# coloured LEDS on front of voice bonnet, for primitive feedback
import adafruit_dotstar
DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6
dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

'''
Maybe later?

button = DigitalInOut(board.D17)
button.direction = Direction.INPUT
button.pull = Pull.UP
'''
# spoken prompts without going back into node red

def curl_speak(phrase):

    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech'''.format(speech = phrase)
    cl_array = cl.split()
    #print(cl_array)
    subprocess.run(cl_array, check=True, capture_output=True).stdout
    return


# main script

config = configparser.ConfigParser()
config.read('etc/mema.ini')

phrase = config['en_prompts']['start_record'].replace(' ','_')
curl_speak(phrase)

dots[2] = (0,0,255)  # red

try:
    subprocess.run(["docker", "stop", "rhasspy"], check=True, capture_output=True, text=True).stdout
except subprocess.CalledProcessError as e:
    raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

# make a file name from the current unix timestamp
unix_time = int(datetime.datetime.now().timestamp())
file_path = config['main']['media_directory'] + "tmp/" + str(unix_time) + ".wav" 

sleep(10)
dots[2] = (255,0,0)  # green

try:
    record_command = config['main']['record_command'] + ' ' + file_path
    record_array = record_command.split()
    #print(' '.join(record_array))
    subprocess.run(record_array, check=True, capture_output=True, text=True).stdout
except subprocess.CalledProcessError as e:
    raise RuntimeError("command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))

dots[2] = (0,0,255)  # red

try:
    subprocess.run(["docker", "start", "rhasspy"], check=True, capture_output=True, text=True).stdout
except subprocess.CalledProcessError as e:
    raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

sleep(10)  # give rhasspy time to reload!

phrase =  config['en_prompts']['end_record'].replace(' ','_')
curl_speak(phrase)

# select speech to text model
model = replicate.models.get("openai/whisper")
# format file as path object (openai needs this)
audio_file = Path(file_path)

# give a little feedback
dots[2] = (0,255,0)  # blue

# speech to text on remote server
# signal transacription empty if something goes wrong
result = {"transcription" : "empty"}
result = model.predict(audio=audio_file)

phrase = config['en_prompts']['end_transcription'].replace(' ','_')
curl_speak(phrase)

# done, feedback, stop blinking lights
dots[2] = (255,0,0)  # green
sleep(5)
dots.deinit()

# delete temporary file
os.remove(file_path)

# return result and file path to intent server
# the format of reply is maintained although this doesn't keep a file
print(result['transcription']  + "|" + 'no_path')
