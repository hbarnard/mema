#!/usr/bin/env python3

from time import sleep
import board
#FIXME: get rid, seems to be incompatilities: import requests
import datetime
import subprocess
from pathlib import Path
import os
from configobj import ConfigObj
import logging
import re
import memalib.mema_utility as mu

# main script
def main():

    config = ConfigObj('etc/mema.ini')
    logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)
        
    # convenience for separating Pi and a random laptop
    pi  = False 
    #FIXME: mema.ini produces strings! also no test on system name now, unreliable    
    if config['main']['pi'] == 'yes' : 
        pi = True

    if pi:
        import board
        # coloured LEDS on front of voice bonnet, for primitive feedback
        from digitalio import DigitalInOut, Direction, Pull
        import adafruit_dotstar
        DOTSTAR_DATA = board.D5
        DOTSTAR_CLOCK = board.D6
        dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)
        dots.deinit()
        
    mu.curl_speak(config['en_prompts']['start_video'])
    
    #FIXME: Actually no need to do this currently, since there's no audio!
    logging.debug('unload docker')
    unix_time = mu.docker_control('stop', 'mema_rhasspy')
    
    #FIXME: libcamera, no audio currently, see extensive web commentary
    true_file_name = str(unix_time) + ".mp4" 
    
    dots[0] = (255,0,0) if pi else None

    video_command = config['main']['video_command']
    true_file_path = config['main']['media_directory'] + "vid/" + true_file_name
    media_path = config['main']['media_directory_url'] + "vid/" + true_file_name   

    try:
        #FIXME: may need adjustment on laptop direct record as silent mp4
        rev_command = re.sub(r"true_file_name", true_file_path, video_command)
        revised_command = re.sub(r"video_maximum", config['main']['video_maximum'], rev_command)
        logging.debug('revised command: ' + revised_command)
        subprocess.call(revised_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        
    dots[0] = (0,0,255) if pi else None
    logging.debug('reload docker start')
    unix_time = mu.docker_control('start', 'mema_rhasspy')
    logging.debug('reload docker end')
    sleep(int(config['main']['rhasspy_reload']))  # give mema_rhasspy time to reload!
    
    mu.curl_speak(config['en_prompts']['end_video'])
    mu.curl_speak(config['en_prompts']['done'])

    # done, feedback, stop blinking lights
    if pi:
        dots[0] = (255,0,0)  # green
        sleep(2)
        dots.deinit()

    text = config['en_literals']['unlabelled_video']
    # return result and file path to intent server
    print(text + "|" + media_path)

if __name__ == '__main__':
    main()



