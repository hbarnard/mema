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
from configobj import ConfigObj

#FIXME: need to adjust the sleep times and recording length!

def main():

    pi  = False 
    #FIXME: mema.ini produces strings! also no test on system name now, unreliable    
    if config['main']['pi'] == 'yes' : 
        pi = True 
        import board
        # coloured LEDS on front of voice bonnet, for primitive feedback
        from digitalio import DigitalInOut, Direction, Pull
        import adafruit_dotstar
        DOTSTAR_DATA = board.D5
        DOTSTAR_CLOCK = board.D6
        dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)
        dots.deinit()
    
    config = ConfigObj('etc/mema.ini')
    logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)

    phrase = config['en_prompts']['start_record'].replace(' ','_')
    mu.curl_speak(phrase)

    # red: feedback before stopping rhasspy
    dots[0] = (0,0,255) if pi else None

    # make a file name from the current unix timestamp
    unix_time = docker_control('stop', 'mema_rhasspy')
    file_path = config['main']['media_directory'] + "tmp/" + str(unix_time) + sys.argv[1] + ".wav" 

    sleep(2)
    # green: ok to talk
    dots[0] = (255,0,0) if pi else None

    try:
        record_command = config['main']['record_command'] + ' ' + file_path
        record_array = record_command.split()
        subprocess.run(record_array, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    # red: end of speech
    dots[0] = (0,0,255) if pi else None

    unix_time = docker_control('start', 'mema_rhasspy')
    sleep(config['main']['rhasspy_reload'])
    mu.curl_speak(config['en_prompts']['end_record'])
    
    result = {"transcription" : config['en_literals']['unlabelled_video']}
    text = ''
    #FIXME: 12/12/2022 test with internal whisper, real-soon
    if config['main']['use_external_ai'] == 'yes' :
        model = replicate.models.get("openai/whisper")
        audio_file = Path(file_path)
        result = model.predict(audio=audio_file)
        text = result['transcription'][:30] 
        mu.curl_speak(config['en_prompts']['end_transcription'])
    else:   
        #FIXME: this block can go to the library, sooner or later
        transcribe_command = config['main']['transcribe_program'] + ' ' + file_path +  ' > /tmp/transcription'
        log.debug('transcribe command is ' + transcribe_command)
        log.debug('result is ' + result)
        subprocess.call(transcribe_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open('/tmp/transcription') as trans: f = trans.read()
        text = f[:30]     
        mu.curl_speak(config['en_prompts']['done'])

    # green: its done
    dots[0] = (255,0,0) if pi else None
    sleep(3)
    dots.deinit()

    # delete temporary files
    os.remove(file_path)

    # return result and file path to intent server
    # the format of reply is maintained although this doesn't keep a file
    print(text  + "|" + 'no_path')

if __name__ == '__main__':
    main()


