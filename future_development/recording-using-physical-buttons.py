import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)   
GPIO.setwarnings(False)

from picamera import PiCamera
import time
from gpiozero import Button, LED
from time import sleep 

camera = PiCamera()
camera.exposure_mode = 'antishake'

camera.start_preview()
camera.resolution = (1280, 960)
camera.brightness = 52
camera.framerate = 30
camera.vflip= True

button1=16                 
LED1=22                    
GPIO.setup(button1,GPIO.IN,pull_up_down=GPIO.PUD_UP) 
GPIO.setup(LED1,GPIO.OUT,) 

BS1=False                  

while(1):                  
        if GPIO.input(button1)==0:            
                print ("Recording in Progress...")
                if BS1==False:                
                        GPIO.output(LED1,True)
                        BS1=True              
                        camera.start_recording("sample1.h264")
                        time.sleep(5)
                else:
                        print ("Recording Stop")
                        GPIO.output(LED1,False)
                        BS1=False
                        sleep()
                        camera.stop_recording()

