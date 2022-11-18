#!/usr/bin/env python3

from pathlib import Path
import replicate
import subprocess

from time import sleep
import datetime
import os

# convenience, test if pi, assumes voice bonnet though!
# therefore may need to change for 'definitive' hardware
pi  = False 

if os.uname()[4].startswith("arm"): 
    pi = True 

if pi:
    import board
    from picamera import PiCamera
    # coloured LEDS on front of voice bonnet, for primitive feedback
    # if no voice bonnet won't need these
    from digitalio import DigitalInOut, Direction, Pull
    import adafruit_dotstar
else:
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    import pygame
    import pygame.camera
    from pygame.locals import *
    pygame.camera.init()

import configparser

# spoken prompts without going back into node red

def curl_speak(phrase):
    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech'''.format(speech = phrase)
    cl_array = cl.split()
    result = subprocess.check_output(cl_array)
    #print(result)
    return

def main():
    if pi:
        DOTSTAR_DATA = board.D5
        DOTSTAR_CLOCK = board.D6
        dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)
        
    config = configparser.ConfigParser()
    config.read('etc/mema.ini')

    if pi: 
        camera = PiCamera()
        camera.resolution = (1024, 768)
        dots[0] = (255,0,0)  # red
    else:
        #print('camera starting') if config['main']['debug'] else None    
        camera = pygame.camera.Camera("/dev/video0",(640,480))
        camera.start()
        
    # can't have this a the moment, no screen
    # camera.start_preview()
    
    # time warm up
    sleep(2)
    
    # make a file name from the current unix timestamp
    unix_time = int(datetime.datetime.now().timestamp())
    file_name = str(unix_time) + ".jpg" 
    
    file_path = config['main']['media_directory'] + "pic/" + file_name
    media_path = config['main']['media_directory_url'] + "pic/" + file_name


    phrase = config['en_prompts']['taking_picture'].replace(' ','_')
    curl_speak(phrase)

    if pi: 
        camera.capture(file_path)
        camera.close()    
        #some feedback remove if no voice bonnet
        dots[0] = (0,255,0)  # red
    else:
        #print('camera getting image') if config['main']['debug'] else None   
        img = camera.get_image()
        pygame.image.save(img,file_path)
    
    sleep(2)

    image_file = Path(file_path)

    # prediction phase
    if pi:
        #some feedback remove if no voice bonnet
        dots[0] = (255,0,0)  # green
        
    sleep(2)
    
    if pi:
        dots.deinit()

    result = 'unlabelled photo'
    if config['main']['use_external_ai']:
        phrase = config['en_prompts']['trying_caption'].replace(' ','_')
        curl_speak(phrase)
        
        #print('using ai caoptioning') if config['main']['debug'] else None   
        model = replicate.models.get("j-min/clip-caption-reward")
        result = model.predict(image=image_file)
            
    print(result  + "|" + media_path)

if __name__ == '__main__':
    main()
    
