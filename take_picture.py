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

# 12/12/2022 now on bullseye uses libcamera command, not Picamera

config = ConfigObj('etc/mema.ini')

pi  = False 
#FIXME: mema.ini produces strings! also no test on system name now, unreliable
if config['main']['pi'] == 'yes' : 
    pi = True     

if pi:
    import board
    from digitalio import DigitalInOut, Direction, Pull
    import adafruit_dotstar
else:
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    import pygame
    import pygame.camera
    from pygame.locals import *
    pygame.camera.init()

def main():
    if pi:
        DOTSTAR_DATA = board.D5
        DOTSTAR_CLOCK = board.D6
        dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

    config = ConfigObj('etc/mema.ini')
    logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)

    if pi: 
        dots[0] = (255,0,0)  # red
    else:
        camera = pygame.camera.Camera("/dev/video0",(640,480))
        camera.start()
    
    # make a file name from the current unix timestamp
    unix_time = int(datetime.datetime.now().timestamp())
    file_name = str(unix_time) + ".jpg" 
    
    file_path = config['main']['media_directory'] + "pic/" + file_name
    media_path = config['main']['media_directory_url'] + "pic/" + file_name
    
    mu.curl_speak(config['en_prompts']['taking_picture'])
    
    if pi: 
        picture_command = config['main']['picture_command'] + ' ' + file_path
        picture_command_array = picture_command.split()
        try:
            subprocess.call(picture_command_array, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        dots[0] = (0,255,0)  # red
    else:
        img = camera.get_image()
        pygame.image.save(img,file_path)
        
    image_file = Path(file_path)

    # prediction phase
    dots[0] = (0,255,0) if pi else None
                    
    result = config['en_literals']['unlabelled_picture']
    
    if config['main']['use_external_ai']  == 'yes':
        mu.curl_speak(config['en_prompts']['trying_caption'])
        model = replicate.models.get("j-min/clip-caption-reward")
        result = model.predict(image=image_file)
        mu.curl_speak(config['en_prompts']['done'])

    dots.deinit() if pi else None
    print(result  + "|" + media_path)

if __name__ == '__main__':
    main()
    
