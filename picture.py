#!/usr/bin/env python3

from pathlib import Path
import replicate

from time import sleep
import datetime

from picamera import PiCamera

# coloured LEDS on front of voice bonnet, for primitive feedback
import adafruit_dotstar
DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6

# not used immediately, but need 'owner' of picture
from databases import Database
database = Database("sqlite:///var/spool/mema/db/memories.db")

camera = PiCamera()
camera.resolution = (1024, 768)

# can't have this at the moment, no screen
# camera.start_preview()
# Camera warm-up time
dots[0] = (255,0,0)  # red

sleep(2)

unix_time = int(datetime.datetime.now().timestamp())
file_path = "/var/spool/mema/pic/" + str(unix_time) + ".jpg" 
#print('taking picture')
camera.capture(file_path)

dots[0] = (0,255,0)  # red
#print('picture taken')

camera.close()
sleep(2)

model = replicate.models.get("j-min/clip-caption-reward")
image_file = Path(file_path)

# prediction phase
dots[0] = (255,0,0)  # red
result = model.predict(image=image_file)
print(result  + "|" + file_path)
