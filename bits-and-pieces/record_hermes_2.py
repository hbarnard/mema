#!/usr/bin/env python
import paho.mqtt.client as mqtt
import wave
import re
import io
MQTThost ='10.0.0.76'
MQTTport = 1883
soundfile = wave.open('audio.wav', 'wb')
soundfile.setframerate(16000)
soundfile.setsampwidth(2)
soundfile.setnchannels(1)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("hermes/asr/startListening")
    client.subscribe("hermes/asr/stopListening")
def on_message(client, userdata, msg):
    print("listening")
    if msg.topic == "hermes/asr/startListening":
      client.subscribe("hermes/audioServer/+/audioFrame")
    elif msg.topic == "hermes/asr/stopListening":
      client.unsubscribe("hermes/audioServer/+/audioFrame")
    elif bool(re.search(r'^hermes\/audioServer\/.*?\/audioFrame$', msg.topic)):
      with io.BytesIO(msg.payload) as wav_buffer:
        with wave.open(wav_buffer, 'rb') as wav:
          audiodata = wav.readframes(wav.getnframes())
          soundfile.writeframes(audiodata)
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTThost, MQTTport, 60)
client.loop_forever()
