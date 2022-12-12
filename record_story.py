#!/usr/bin/env python3

from time import sleep
import board
import subprocess
#import requests
import datetime
from pathlib import Path
import os
import re
import memalib.mema_utility as mu
import replicate
from configobj import ConfigObj
import logging

# main script
def main():

    config = ConfigObj('etc/mema.ini')
    logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)
    
    pi  = False 
    # no test on system name now, unreliable    
    if config['main']['pi']: 
        pi = True 
        import board
        # coloured LEDS on front of voice bonnet, for primitive feedback
        from digitalio import DigitalInOut, Direction, Pull
        import adafruit_dotstar
        DOTSTAR_DATA = board.D5
        DOTSTAR_CLOCK = board.D6
        dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

    mu.curl_speak(config['en_prompts']['start_record'])    
    unix_time = mu.docker_control('stop', 'mema_rhasspy')
    file_name = str(unix_time) + ".wav" 
    
    file_path = config['main']['media_directory'] + "rec/" + file_name
    media_path = config['main']['media_directory_url'] + "rec/" + file_name
    
    dots[0] = (255,0,0) if pi else None

    try:
        #FIXME: this all goes wrong because of the comma -D Hw3,0 for example: see: https://github.com/shivammathur/setup-php/issues/392
        record_command = config['main']['record_command'] + ' ' + config['main']['audio_maximum'] + ' ' + file_path
        #record_array = record_command.split()
        logging.debug('record command is: ' + record_command)
        subprocess.call(record_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    dots[0] = (0,0,255)  if pi else None  # red

    unix_time = mu.docker_control('start', 'mema_rhasspy')
    sleep(int(config['main']['rhasspy_reload']))  # give mema_rhasspy time to reload!
    
    mu.curl_speak(config['en_prompts']['end_record'])

    # give a little feedback
    dots[0] = (0,255,0)  if pi else None
    
    text = config['en_literals']['unlabelled_audio']
   
    #FIXME speech to text on remote server, replace with whisper.cpp cron
    if config['main']['use_external_ai']:
        # select speech to text model
        model = replicate.models.get("openai/whisper")
        # format file as path object (openai needs this)
        audio_file = Path(file_path)
        result = model.predict(audio=audio_file)
        text = result['transcription'] 
        mu.curl_speak(config['en_prompts']['end_transcription'])
        
    mu.curl_speak(config['en_prompts']['done'])

    # done, feedback, stop blinking lights
    if pi:
        dots[0] = (255,0,0)  # green
        dots.deinit()
    
    # return result and file path to intent server
    print(text + "|" + media_path)

if __name__ == '__main__':
    main()



