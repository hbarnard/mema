#!/usr/bin/env python3

from time import sleep
import board
import subprocess
#import requests
import datetime
from pathlib import Path
import os
#from plumbum import local, FG, BG

import replicate

import configparser

# convenience for separating Pi and a random laptop
pi = False
if os.uname()[4].startswith("arm"): 
    pi = True 

if pi:
    import board
    from picamera import PiCamera
    # coloured LEDS on front of voice bonnet, for primitive feedback
    from digitalio import DigitalInOut, Direction, Pull
    import adafruit_dotstar
    DOTSTAR_DATA = board.D5
    DOTSTAR_CLOCK = board.D6
    dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)


# spoken prompts without going back into node red

def curl_speak(phrase):
    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech > /dev/null'''.format(speech = phrase)
    cl_array = cl.split()
    subprocess.call(cl_array,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return


# main script
def main():
    dots = {}
    config = configparser.ConfigParser()
    config.read('etc/mema.ini')

    phrase = config['en_prompts']['start_record'].replace(' ','_')
    curl_speak(phrase)
    sleep(1)

    try:
        subprocess.run(["docker", "stop", "mema_rhasspy"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    # make a file name from the current unix timestamp
    unix_time = int(datetime.datetime.now().timestamp())
    file_name = str(unix_time) + ".wav" 
    
    file_path = config['main']['media_directory'] + "rec/" + file_name
    media_path = config['main']['media_directory_url'] + "rec/" + file_name

    sleep(1)
    if pi:
        dots[0] = (255,0,0)  # green

    try:
        record_command = config['main']['record_command'] + ' ' + file_path
        record_array = record_command.split()
        subprocess.call(record_array, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    if pi:
        dots[0] = (0,0,255)  # red

    try:
        subprocess.run(["docker", "start", "mema_rhasspy"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    sleep(5)  # give mema_rhasspy time to reload!

    phrase =  config['en_prompts']['end_record'].replace(' ','_')
    curl_speak(phrase)



    # give a little feedback
    if pi:
        dots[0] = (0,255,0)  # blue

    # probably in configuration later
    text = 'no label'
   
    # speech to text on remote server
    if config['main']['use_external_ai']:
        # select speech to text model
        model = replicate.models.get("openai/whisper")
        # format file as path object (openai needs this)
        audio_file = Path(file_path)
        result = model.predict(audio=audio_file)
        text = result['transcription'] 
        phrase = config['en_prompts']['end_transcription'].replace(' ','_')
    else:        
        phrase = config['en_prompts']['done']
        curl_speak(phrase)

    # done, feedback, stop blinking lights
    if pi:
        dots[0] = (255,0,0)  # green
        dots.deinit()
    
    # return result and file path to intent server
    print(text + "|" + media_path)

if __name__ == '__main__':
    main()



