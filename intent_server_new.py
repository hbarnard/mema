from fastapi import FastAPI, Request
import sys
import os

# for system health, but pycurl should be used elsewhere
# get rid of one of these, pycurl_request is probably problematic
import pycurl
import pycurl_requests as req
from io import BytesIO

# get rid of one of these too, keep subprocess if possible
import subprocess
from plumbum import FG, BG, local

import datetime
from pathlib import Path
import requests


from fastapi import UploadFile, File, Form
from fastapi import APIRouter, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import re

import sqlite3


import configparser

# spoken prompts without going back into node red
def curl_speak(phrase):
    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech > /dev/null'''.format(speech = phrase)
    cl_array = cl.split()
    subprocess.call(cl_array,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return

# this needs to be elsewhere but 'for the moment'

def system_health():

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(pycurl.FAILONERROR, 0)

    # don't test the intent server, used for this display!
    mema_servers = {
        'rhasspy'  :  config['main']['rhasspy_main'],
        'mimic3'   :  config['main']['mimic3'],
        'node_red' :  config['main']['node_red']
    }

    mema_health = {}
    for name,url  in mema_servers.items():
        try:
            c.setopt(c.URL, url)
            c.perform()
            if (c.getinfo(c.RESPONSE_CODE) == 200):
                mema_health[name] = 'dotgreen'
            else:
                mema_health[name] = 'dotred'
        except:
            mema_health[name] = 'dotred'
    c.close()
    return mema_health



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

@app.post("/")
async def info(info : Request):
    
    req_info = await info.json()
    
    raw_speech = req_info['input'] 
    intent     = req_info['intent']['intentName'] 
    number     = re.findall(r'\b\d+\b', raw_speech) 
    please     = re.findall(r'\bplease\b', raw_speech)  
    
        
    if not len(intent) or (req_info['asrConfidence'] < float(config['main']['confidence'])) :
        curl_speak(config['en_prompts']['not_understood'])
        return {
            "status" : "FAIL"
        }
    

    
    print(req_info) if config['main']['debug'] else None
    
    # one or two, such as redirects can't be handled in the intent table
    if intent == "GetStory":
        url = config['main']['intent_server'] + "/memory/" + str(story_number[0]) + "/speak"
        return RedirectResponse(url)    
    
    # intents are the options see: https://stackoverflow.com/questions/17881409/whats-an-alternative-to-if-elif-statements-in-python
    {

        'TakePhoto'  : run_photo_command,
        'TellStory'  : print("tell story found"),   
        'Associate'  : print("associate photo and story found"),
        'RecordStory': run_record_command,
        'RecordVideo': run_video_command,
        'KillVideo'  : run_kill_video_command,  
        'LabelVideo' : run_label_video_command,       
        'SlicePie'   : run_pie,
        'DuckDuck'   : run_search_command            

    }[intent](number,please)
    
    req_info = ''   
 
    print("command done") if config['main']['debug'] else None
    
    return {
        "status" : "SUCCESS",
        "data" : req_info
    }


def notAfun():
  print ("not a valid function name")


# take a photo and store it
            
def run_photo_command(number,please):
    
    print("take photo found") if config['main']['debug'] else None
        
    cur = con.cursor()
    picture = local[config['main']['picture_program']]
    result = picture()
    (text, file_path) = result.split('|')

    unix_time = int(datetime.datetime.now().timestamp())
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (text, text, file_path, unix_time, 0, 1, 'photo'))
    con.commit()
    print("photo command done") if config['main']['debug'] else None
    return 

# record audio and store it
    
def run_record_command(number,please):
    
    print("record story found") if config['main']['debug'] else None
    
    result = subprocess.check_output(config['main']['story_program'])
    result_string = result.decode('utf-8')

    (text, file_path) = result_string.split('|')
    
    unix_time = int(datetime.datetime.now().timestamp())
    description = text[0:30]
    
    cur = con.cursor()
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (description, text, file_path, unix_time, 0, 1, 'text'))
    con.commit()
    return text  
    
# doesn't work properly on laptop  

# record video and store it
  
def run_video_command(number,please):
    
    print("record video found") if config['main']['debug'] else None
    
    unix_time = int(datetime.datetime.now().timestamp())    
    
    # make and add file path    
    file_path = config['main']['media_directory'] + 'vid/' + str(unix_time) + '.mp4'     
    video_command = config['main']['video_command'] + ' ' +  file_path
   
    try:
        subprocess.call(video_command, shell=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        
    #FIXME: how to deal with this, Google cloud?
    description = 'unlabelled video'
    text = 'unlabelled video'
    
    cur = con.cursor()
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (description, text, file_path, unix_time, 0, 1, 'video'))
    con.commit()
    return text      



# ad-hoc remedy for non working video on laptop

# bodge kill cvlc video process

def run_kill_video_command(number,please):
    
    print("kill video record found") if config['main']['debug'] else None
    
    com_array = config['main']['kill_video_command'].split()
    subprocess.call(com_array,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return


# shares code with transcribe and needs external AI, at present

# label video in database
   
def run_label_video_command(number,please):
    
    print("label video found") if config['main']['debug'] else None
    cur = con.cursor()
    result = cur.execute("SELECT * FROM memories WHERE memory_id=?",(video_number))
    fields = result.fetchone()
    if fields is not None:
        if (fields[7] != 'video'):
            curl_speak(config['en_prompts']['not_video'])
            return
        else:
            result = subprocess.run([config['main']['label_program']],  stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
            #print(result)
            (text, file_path) = result.split('|')
            if (text != 'empty'):
                cur.execute("update memories set description = ? WHERE memory_id=?",(text, video_number[0]))
                con.commit()
            else:
                curl_speak(config['en_prompts']['didnt_get'])
    else:
        curl_speak(config['en_prompts']['sorry'])
    print(fields)
    return


# to be done
    
def run_associate_command(number,please):
    print("running classifier") if config['main']['debug'] else None
    s2_out = subprocess.check_output([sys.executable, "/home/pi/projects/mema/associate.py"])
    return s2_out    
 

# skeletion get search page, see https://community.rhasspy.org/t/recognized-untrain-sentences-words/465/5
# discussion of wildcards

def run_search_command(number,please):

    r = req.get('https://duckduck.com?q=hughbarnard')
    #xdg-open https://google.com
    print(r.text)
    if (r.status_code == 200):
        print(r.text)
        return TEMPLATES.TemplateResponse(
        "search.html",
        {"request": r, "content": r.text}
    )
    else:
        return

def run_pie(number,please):
    return
  
# screen only section

# testing only, make sure favicon isn't constantly 404ed

@app.get('/favicon.ico')
async def favicon():
   return FileResponse('./static/favicon.ico')
 

# list of memories to screen    

@app.get("/memories")
def fetch_all(request: Request):
    cur = con.cursor()
    servers = []
    # result = cur.execute("SELECT * FROM memories")
    result = cur.execute("select memory_id, description, text, file_path, strftime('%d-%m-%Y %H:%M', unix_time, 'unixepoch') as date, public from memories")

    results = result.fetchall()
    return TEMPLATES.TemplateResponse(
        "list.html",
        {"request": request, "results" :results, "mema_health": system_health()}
    )


# get memory to screen

@app.get("/memory/{id}")
def fetch_data(request: Request, id: int):
    
    cur = con.cursor()
    result = cur.execute("SELECT * FROM memories WHERE memory_id={}".format(str(id)))
    fields = result.fetchone()
    return TEMPLATES.TemplateResponse(
        "memory.html",
        {"request": request,  "fields": fields}
    )

# ok ugly should be get, but problem with FastApi see: 
# https://stackoverflow.com/questions/62119138/how-to-do-a-post-redirect-get-prg-in-fastapi

@app.post("/memory/{id}/speak")
def fetch_data(id: int):
    cur = con.cursor()
    result = cur.execute("SELECT text FROM memories WHERE memory_id={}".format(str(id)))
    fields = result.fetchone()
    if fields is not None:
        lines = fields[0].splitlines()
        text = ' '.join(lines)
        phrase = text.replace(' ','_')
        curl_speak(phrase)
    else:
        curl_speak(config['en_prompts']['sorry'])
    return fields

     
    
    
