#!/usr/bin/env python3

import os
import sys

from time import sleep
import board
import subprocess
import requests
import datetime
from pathlib import Path
import logging
import replicate
import sys
from configobj import ConfigObj
import memalib.mema_utility
from digitalio import DigitalInOut, Direction, Pull

# coloured LEDS on front of voice bonnet, for primitive feedback
import adafruit_dotstar
from configobj import ConfigObj

#FIXME: need to adjust the sleep times and recording length!

def main():

    DOTSTAR_DATA = board.D5
    DOTSTAR_CLOCK = board.D6
    dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)
    
    config = ConfigObj('etc/mema.ini')
    logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)

    phrase = config['en_prompts']['start_record'].replace(' ','_')
    curl_speak(phrase)

    #feedback before stopping rhasspy
    dots[2] = (0,0,255)  # red

    # make a file name from the current unix timestamp
    unix_time = docker_control('stop', 'mema_rhasspy')
    file_path = config['main']['media_directory'] + "tmp/" + str(unix_time) + sys.argv[1] + ".wav" 

    sleep(10)
    dots[2] = (255,0,0)  # green

    try:
        record_command = config['main']['record_command'] + ' ' + file_path
        record_array = record_command.split()
        subprocess.run(record_array, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    dots[2] = (0,0,255)  # red

    unix_time = docker_control('start', 'mema_rhasspy')
    sleep(config['main']['rhasspy_reload'])
    curl_speak(config['en_prompts']['end_record'])

    # give a little feedback
    dots[2] = (0,255,0)  # blue
    
    result = {"transcription" : "empty"}
    #FIXME: 12/12/2022 replace with internal whisper, real-soon
    if config['main']['use_external_ai']:
        # select speech to text model
        model = replicate.models.get("openai/whisper")
        audio_file = Path(file_path)
        result = model.predict(audio=audio_file)
        text = result['transcription'] 
        curl_speak(config['en_prompts']['end_transcription'])
    else:        
        curl_speak(config['en_prompts']['done'])

    # done, feedback, stop blinking lights
    dots[2] = (255,0,0)  # green
    sleep(5)
    dots.deinit()

    # delete temporary file
    os.remove(file_path)

    # return result and file path to intent server
    # the format of reply is maintained although this doesn't keep a file
    print(result['transcription']  + "|" + 'no_path')

if __name__ == '__main__':
    main()


