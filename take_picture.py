#!/usr/bin/env python3

from pathlib import Path
import replicate
from time import sleep
import datetime
import subprocess
import os
from configobj import ConfigObj
import memalib.mema_utility as mu
import logging

def main():
    dots = {}
    pi  = False 
    
    #FIXME: 12/12/2022 Pi now on bullseye uses libcamera command, not Picamera
    try:
        config = ConfigObj('etc/mema.ini')
        #print(config)
    except:
        print('config load failed in take_picture.py')

    # this is a hack to make sure we have ENV everywhere we need it
    my_env = mu.get_env(config['main']['env_file'])
    logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)


    #FIXME: mema.ini produces strings! also no test on system name now, unreliable
    if config['main']['pi'] == 'yes' : 
        pi = True     

    if pi:
        import board
        from digitalio import DigitalInOut, Direction, Pull
        import adafruit_dotstar
        DOTSTAR_DATA = board.D5
        DOTSTAR_CLOCK = board.D6
        dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)
        dots[0] = (255,0,0)  # red?
    
    # make a file name from the current unix timestamp
    unix_time = int(datetime.datetime.now().timestamp())
    file_name = str(unix_time) + ".jpg" 
    
    file_path = config['main']['media_directory'] + "pic/" + file_name
    media_path = config['main']['media_directory_url'] + "pic/" + file_name
    
    mu.curl_speak(config['en_prompts']['taking_picture'])
    
    picture_command = config['main']['picture_command'] + ' ' + file_path
    picture_command_array = picture_command.split()
    
    try:
        subprocess.call(picture_command_array, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logging.debug('taking picture error')
        raise RuntimeError("command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    
    if pi:
        dots[0] = (0,255,0)  # red
        # prediction phase
        dots[0] = (0,255,0) if pi else None
                    
    result = config['en_literals']['unlabelled_picture']
    
    if config['main']['use_external_ai']  == 'yes':
        mu.curl_speak(config['en_prompts']['trying_caption'])
        api = replicate.Client(api_token=my_env['REPLICATE_API_TOKEN'])
        model = api.models.get("j-min/clip-caption-reward")
        image_file = Path(file_path)
        result = model.predict(image=image_file)
        mu.curl_speak(config['en_prompts']['done'])
    else:
        mu.curl_speak(config['en_prompts']['done'])

    dots.deinit() if pi else None
    print(result  + "|" + media_path)

if __name__ == '__main__':
    main()
    
