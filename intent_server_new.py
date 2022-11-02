from fastapi import FastAPI, Request
import sys
import os

# for system health, but pycurl should be used elsewhere
import pycurl
from io import BytesIO


import subprocess
import datetime
import requests

from fastapi import UploadFile, File, Form
from fastapi import APIRouter, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import re

import sqlite3
from pathlib import Path

import configparser

from digitalio import DigitalInOut, Direction, Pull
import adafruit_dotstar


def clear_dots()

    DOTSTAR_DATA = board.D5
    DOTSTAR_CLOCK = board.D6
    dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)
    dots.deinit()
    return 


# spoken prompts without going back into node-red

def curl_speak(phrase):

    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech'''.format(speech = phrase)
    cl_array = cl.split()
    #print(cl_array)
    subprocess.run(cl_array, check=True, capture_output=True).stdout
    return



# this needs to be elsewhere but 'for the moment'

def system_health():

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(pycurl.FAILONERROR, 0)

    # don't test the intent server, used for this display!
    mema_servers = {
    'rhasspy_main':'http://10.0.0.76:12101',
    'mimic3':'http://10.0.0.76:59125',
    'node_red':'http://10.0.0.76:1880'

    }

    mema_health = {}

    for name,url  in mema_servers.items():
        try:
            c.setopt(c.URL, url)
            c.perform()
            #print(name + ' ' + 'Response Code: %d' % c.getinfo(c.RESPONSE_CODE))
            if (c.getinfo(c.RESPONSE_CODE) == 200):
                mema_health[name] = 'dotgreen'
            else:
                mema_health[name] = 'dotred'
        except:
            #print(name + ' ' + 'no connection')
            mema_health[name] = 'dotred'

    #Ending the session and freeing the resources
    c.close()
    return mema_health

# main here, change to main() in a while



# ugly but make sure LEDS are cleared when this starts or restarts
clear_dots()

config = configparser.ConfigParser()
config.read('etc/mema.ini')


con = sqlite3.connect(config['main']['db'], check_same_thread=False)

app = FastAPI(debug=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="static/media", html=True), name="media")   


BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates"))

api_router = APIRouter()


# integrate and put into config file.
'''
log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
uvicorn.run(app, log_config=log_config)
uvicorn.run(app, host="0.0.0.0", port=8000, log_config=log_config)
'''

'''
or start to use an url for each intent
def handle_one():
  do_stuff

def handle_two():
  do_stuff

def handle_three():
  do_stuff


{'one': handle_one, 
 'two': handle_two, 
 'three': handle_three}[option]()
'''





# Python 3.10 has 'match' which would tidy this up a little.
# needs tidying anyway

@app.post("/")
async def getInformation(info : Request):
    
    req_info = await info.json()
    intent = req_info['intent']['intentName']
    raw_speech = req_info['input']
    #print(req_info)
    #print(req_info['asrConfidence'])
    
    
    # if there's no intent from sentences.ini or the confidence level of the speech is under
    # the level in etc/mema.ini say it can't be understood
    
    if not len(intent) or (req_info['asrConfidence'] < float(config['main']['confidence'])) :
        curl_speak(config['en_prompts']['not_understood'])
        return {
            "status" : "FAIL"
        }
    if intent == "TakePhoto":
        print("take photo found")
        run_picture_command()
    elif intent == "GetStory":
        print("get story found")
        story_number = re.findall(r'\b\d+\b', raw_speech)
        #print(story_number[0])
        url = config['main']['intent_server'] + "/memory/" + str(story_number[0]) + "/speak"
        return RedirectResponse(url)
    elif intent == "TellStory":
        print("tell story found")    
    elif intent == "Associate":
        print("associate photo and story found")
    elif intent == "StoreStory":
        run_record_command()
        #print("record story found")
    elif intent == "RecordVideo":
        story_number = re.findall(r'\b\d+\b', raw_speech)
        run_video_command()  
    elif intent == "LabelVideo":
        video_number = re.findall(r'\b\d+\b', raw_speech)
        run_label_video_command(video_number)        
        #print("label video found for " + str(video_number))
    elif intent == "SlicePie":
        please = re.findall(r'\bplease\b', raw_speech)
        #print('please is '  + please[0])
        if not please:
            curl_speak(config['en_prompts']['nope'])
        else:
            curl_speak(config['en_prompts']['ok_then'])                        
    else:
        print("nothing found")        
    return {
        "status" : "SUCCESS",
        "data" : req_info
    }
    
def run_picture_command():
    cur = con.cursor()
    result = subprocess.run([config['main']['picture_program']], check=True, capture_output=True, text=True).stdout
    (text, file_path) = result.split('|')

    unix_time = int(datetime.datetime.now().timestamp())
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (text, text, file_path, unix_time, 0, 1, 'photo'))
    con.commit()
    return text
    
def run_record_command():
    result = subprocess.run([config['main']['story_program']],  check=False, capture_output=True, text=True).stdout
    #print(result)
    (text, file_path) = result.split('|')
    
    unix_time = int(datetime.datetime.now().timestamp())
    description = text[0:30]
    
    cur = con.cursor()
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (description, text, file_path, unix_time, 0, 1, 'text'))
    con.commit()
    return text  
    
def run_video_command():
    
    unix_time = int(datetime.datetime.now().timestamp())    
    
    # make and add file path    
    file_path = config['main']['media_directory'] + 'vid/' + str(unix_time) + '.mp4'     
    video_command = config['main']['video_command'] + ' ' +  file_path
   
    try:
        subprocess.run(video_command, shell=True, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        
    #FIXME: how to deal with this, Google cloud?
    description = 'unlabelled video'
    text = 'unlabelled video'
    
    cur = con.cursor()
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (description, text, file_path, unix_time, 0, 1, 'video'))
    con.commit()
    return text      
    
def run_label_video_command(video_number):
    cur = con.cursor()
    result = cur.execute("SELECT * FROM memories WHERE memory_id=?",(video_number))
    fields = result.fetchone()
    if fields is not None:
        if (fields[7] != 'video'):
            curl_speak(config['en_prompts']['not_video'])
            return
        else:
            result = subprocess.run([config['main']['label_program']],  check=True, capture_output=True, text=True).stdout
            #print(result)
            (text, file_path) = result.split('|')
            if (text != 'empty'):
                #print('video number is ' + video_number)
                cur.execute("update memories set description = ? WHERE memory_id=?",(text, video_number[0]))
                con.commit()
            else:
                curl_speak(config['en_prompts']['didnt_get'])
    else:
        curl_speak(config['en_prompts']['sorry'])
    print(fields)
    return

    
def run_associate_command():
    print("running classifier")
    s2_out = subprocess.check_output([sys.executable, "/home/pi/projects/mema/associate.py"])
    return s2_out    
 
@app.get('/favicon.ico')
async def favicon():
   return FileResponse('./static/favicon.ico')
 
    
# screen only
@app.get("/memory/{id}")
def fetch_data(id: int):
    cur = con.cursor()
    result = cur.execute("SELECT * FROM memories WHERE memory_id={}".format(str(id)))
    fields = result.fetchone()
    return fields
    
@app.get("/memories")
def fetch_all(request: Request):
    cur = con.cursor()
    servers = []
    result = cur.execute("SELECT * FROM memories")
    results = result.fetchall()
    return TEMPLATES.TemplateResponse(
        "list.html",
        {"request": request, "results" :results, "mema_health": system_health()}
    )


# ok ugly should be get, but problem with FastApi see: 
# https://stackoverflow.com/questions/62119138/how-to-do-a-post-redirect-get-prg-in-fastapi
@app.post("/memory/{id}/speak")
def fetch_data(id: int):
    cur = con.cursor()
    result = cur.execute("SELECT text FROM memories WHERE memory_id={}".format(str(id)))
    fields = result.fetchone()
    if fields is not None:
        #print(fields)
        lines = fields[0].splitlines()
        text = ' '.join(lines)
        phrase = text.replace(' ','_')
        curl_speak(phrase)
    else:
        curl_speak(config['en_prompts']['sorry'])
    return fields


     
    
    