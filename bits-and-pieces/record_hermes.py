#!/usr/bin/python3

import time
import sys
import os
import paho.mqtt.client as paho
import wave
import io
import pyaudio
broker = "localhost"

output = io.BytesIO()
p = pyaudio.PyAudio()
streamOut = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    output=True)

# if not os.path.exists(folder):
#     os.makedirs(folder)
# os.system('rm ' + folder + '/*')


def on_message(client, userdata, message: paho.MQTTMessage):
    print(message.payload)
  #  wf2 = wave.open(io.BytesIO(message.payload), 'rb')
    with io.BytesIO(message.payload) as wav_buffer:
      with wave.open(wav_buffer, 'rb') as wav:
        # print(wav.getsampwidth())
        data2 = wav.readframes(wav.getnframes())
        waveFile.writeframes(data2) 

  #    data2 = wf2.readframes(wf2.getnframes())
#    streamOut.write(data2)

    # print(message.payload)
        time.sleep(1)
        print("received message =", str(message.payload.decode("utf-8")))

    # millis = int(round(time.time() * 1000))

    # f = open(file_name + str(millis) + '.wav', 'wb')
    # f.write(message.payload)
    # f.close()
#client_id="", clean_session=True, userdata=None,
#            protocol=MQTTv311, transport="tcp"

# client = paho.Client(client_id="client-001", transport="websockets" )
client = paho.Client(client_id="client-001", clean_session=True, transport="tcp")
client.on_message = on_message

#####
print("connecting to broker ", broker)
#client.username_pw_set('<USER>', '<PASS>')
client.connect(broker)  # connect
print("subscribing ")
client.subscribe("hermes/audioServer/office/audioFrame", qos=2)  # subscribe

client.loop_start()  # start loop to process received messages

waveFile = wave.open("/var/spool/mema/rec/test.wav", "wb")
waveFile.setnchannels(1)
waveFile.setsampwidth(2)
waveFile.setframerate(16000)


#time.sleep(4)
#waveFile.close()
#client.disconnect()  # disconnect
#client.loop_stop()  # stop loop

#print("for f in ./tmp/*.wav; do echo \"file '$f'\" >> mylist.txt; done")
#print("ffmpeg -f concat -safe 0 -i mylist.txt -c copy output.wav")
