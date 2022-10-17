import pyaudio

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

'''
pi@picroft:~/projects/mema $ arecord -f cd -c 2 -D dsnooped foobar.wav
Recording WAVE 'foobar.wav' : Signed 16 bit Little Endian, Rate 44100 Hz, Stereo
Warning: rate is not accurate (requested = 44100Hz, got = 48000Hz)
         please, try the plug plugin (-Dplug:dsnooped)
         
curl -X POST --data 'Hello You Silly Billies.' --output - localhost:12101/api/text-to-speech | /usr/bin/aplay
         
         
         
'''
