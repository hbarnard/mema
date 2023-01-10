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
import logging
from configobj import ConfigObj

import memalib.mema_utility as mu



# spoken prompts without going back into node red

def curl_speak(phrase):
    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech > /dev/null'''.format(speech = phrase)
    cl_array = cl.split()
    subprocess.call(cl_array,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return


# main script
def main():
    dots = {}
    config = ConfigObj('etc/mema.ini')
        
    # this is a hack to make sure we have ENV everywhere we need it, especially 'REPLICATE_API_TOKEN
    my_env = mu.get_env(config['main']['env_file'])
    
    logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)

    # convenience for separating Pi and a random laptop
    pi  = False 
    # no test on system name in os now, unreliable, Pi changed from arm to aaarch    
    if config['main']['pi'] == 'yes' : 
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
    
    mu.curl_speak(config['en_prompts']['start_record'])
    sleep(1)

    try:
        subprocess.run(["sudo","docker", "stop", "mema_rhasspy"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        record_command = config['main']['record_command'] + ' ' + config['main']['audio_maximum'] + ' ' + file_path
        #print('record command is: ' + record_command)
        logging.debug('record command is: ' + record_command)
        record_array = record_command.split()
        subprocess.call(record_array, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logging.debug('record command failed: ' + e.output)
        raise RuntimeError("command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    if pi:
        dots[0] = (0,0,255)  # red

    try:
        subprocess.run(["sudo","docker", "start", "mema_rhasspy"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    sleep(5)  # give mema_rhasspy time to reload!
    mu.curl_speak(config['en_prompts']['end_record'])

    # give a little feedback
    if pi:
        dots[0] = (0,255,0)  # blue

    # probably in configuration later
    text = config['en_literals']['unlabelled_audio']
   
    # speech to text on remote server
    if config['main']['use_external_ai']:
        #logging.debug('in record transcribe')
        
        # use whisper.cpp in the mema home directory, for example /home/pi/whisper.cpp for transacription
        
        # FIXME: Downsample necessary on Thinkpad, because it misreports 16khz 
        # see https://acassis.wordpress.com/2012/12/07/testing-if-your-sound-card-can-record-at-16khz-needed-by-some-voice-recognition-engines/
        revised_command = config['main']['downsample_command'].replace("file_path", file_path)
        subprocess.call(revised_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # FIXME: This will probably be too slow on the Pi4, see possible use of etc/cron/transcribe_audio.py instead
        subprocess.call(config['main']['transcribe_program'], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.debug('finished transcribe ')
        t = open("/tmp/tmp.wav.txt", "r") 
        text = t.read() 
        text = ' '.join(text.splitlines())
        t.close()
        os.unlink("/tmp/tmp.wav.txt")
        os.unlink("/tmp/tmp.wav")
        
        # or use external speech to text model on replicate.com
        '''
        audio_file = Path(file_path)
        api = replicate.Client(api_token=my_env['REPLICATE_API_TOKEN'])
        model = api.replicate.models.get("openai/whisper")
        image_file = Path(file_path)
        result = model.predict(audio=audio_file)
        text = result['transcription']        
        '''
        
        logging.debug('finished transcribe: ' + text)
        mu.curl_speak(config['en_prompts']['end_transcription'])
        
    mu.curl_speak(config['en_prompts']['done'])

    # done, feedback, stop blinking lights
    if pi:
        dots[0] = (255,0,0)  # green
        dots.deinit()
    
    # return result and file path to intent server
    logging.debug('return transcribe: ' + text + ' ' + media_path)
    print(text + "|" + media_path)

if __name__ == '__main__':
    main()



