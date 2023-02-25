#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import wave
import re
import io


from time import sleep
import subprocess
import os
import logging
from configobj import ConfigObj


host ='localhost'
port = 1883

soundfile = wave.open('/tmp/search.wav', 'wb')
soundfile.setframerate(16000)
soundfile.setsampwidth(2)
soundfile.setnchannels(1)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("hermes/asr/startListening")
    client.subscribe("hermes/asr/stopListening")

def on_message(client, userdata, msg):
    #print("listening")
    if msg.topic == "hermes/asr/startListening":
        print('start listening')
        client.subscribe("hermes/audioServer/+/audioFrame")
        
    elif msg.topic == "hermes/asr/stopListening":
        print('stop listening')
        text = transcribe(userdata)
        client.unsubscribe("hermes/audioServer/+/audioFrame")
        logging.debug('text is ' + text )
    elif bool(re.search(r'^hermes\/audioServer\/.*?\/audioFrame$', msg.topic)):
        with io.BytesIO(msg.payload) as wav_buffer:
            with wave.open(wav_buffer, 'rb') as wav:
                audiodata = wav.readframes(wav.getnframes())
                soundfile.writeframes(audiodata)

def transcribe(config):
    try:
        downsample_command = config['main']['downsample_command'].replace('file_path', '/tmp/search.wav')
        #logging.debug('downsample ' + downsample_command)
        os.remove("/tmp/tmp.wav")
        subprocess.call(downsample_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        #logging.debug('transcribe ' + config['main']['transcribe_program'])
        subprocess.call(config['main']['transcribe_program'], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        raise RuntimeError("downsample command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))

    #logging.debug('finished transcribe ')
    t = open("/tmp/tmp.wav.txt", "r") 
    text = t.read() 
    text = ' '.join(text.splitlines())
    t.close()
    return text

def get_data(text):
    return

          
          
def main():
    try:
        config = ConfigObj('etc/mema.ini')
        #print(config)
    except:
        print('config load failed in take_picture.py')
    logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)
              
    client = mqtt.Client(userdata=config)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port, 60)
    client.loop_forever()


if __name__ == '__main__':
    main()
