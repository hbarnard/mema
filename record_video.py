#!/usr/bin/env python3

from time import sleep
import board
import subprocess
import requests
import datetime
from pathlib import Path
import os
from plumbum import local, FG, BG

import configparser
import re

#FIXME: we need this currently because the video doesn't end cleanly
# see: https://stackoverflow.com/questions/69197470/how-to-use-threads-inside-a-class-that-act-as-a-countdown-timer
# for construction, put into library later on

class UserTimer:
    def __init__(self, id=None, current_status=None, interval=5):
        self.id = id
        self.current_status = current_status
        self.interval = interval

    def timeout(self):
        print("time over for", self.id)

    def __call__(self):
        self.timer_thread = Timer(self.interval, self.timeout)
        self.timer_thread.start()

    def cancel(self):
        try:
            self.timer_thread.cancel()
        except AttributeError:
            raise RuntimeError("'UserTimer' object not started.")


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


#FIXME: spoken prompts without going back into node red
# can do this via Rhasspy, more integrated since changing central config would change spoken choice

def curl_speak(phrase):
    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech > /dev/null'''.format(speech = phrase)
    cl_array = cl.split()
    subprocess.call(cl_array,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return


# main script
def main():

    config = configparser.ConfigParser()
    config.read('etc/mema.ini')

    phrase = config['en_prompts']['start_video'].replace(' ','_')
    curl_speak(phrase)
    sleep(1)

    try:
        subprocess.run(["docker", "stop", "rhasspy"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    # make a file name from the current unix timestamp
    unix_time = int(datetime.datetime.now().timestamp())
    file_name = str(unix_time) + ".avi" 
    
    file_path = config['main']['media_directory'] + "vid/" + file_name
    media_path = config['main']['media_directory_url'] + "vid/" + file_name

    sleep(1)
    if pi:
        dots[0] = (255,0,0)  # green

    video_command = config['main']['video_command']

    try:
        if pi:
            subprocess.call(video_command)
        else:
            rev_command = re.sub(r"file_name", file_path, video_command)
            revised_command = re.sub(r"video_maximum", config['main']['video_maximum'], rev_command)
            subprocess.call(revised_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(revised_command)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        
    text = 'unlabelled video'

    if pi:
        dots[0] = (0,0,255)  # red

    try:
        subprocess.run(["docker", "start", "rhasspy"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    sleep(5)  # give rhasspy time to reload!

    phrase =  config['en_prompts']['end_record'].replace(' ','_')
    curl_speak(phrase)
   
    # FIXME: No analysis for video at present
    # if config['main']['use_external_ai']:
    #    result = model.predict(audio=audio_file)
    #    text = result['transcription'] 
    #    phrase = config['en_prompts']['end_transcription'].replace(' ','_')
        
    #phrase = config['en_prompts']['done']
    #curl_speak(phrase)

    # done, feedback, stop blinking lights
    if pi:
        dots[0] = (255,0,0)  # green
        dots.deinit()

    # probably in configuration later
    text = 'no label'
        
    # return result and file path to intent server
    print(text + "|" + media_path)

if __name__ == '__main__':
    main()



