from fastapi import FastAPI, Request
import sys
import os, pwd

#FIXME: this isn't really the answer either
import webbrowser as wb

# for system health, but pycurl should be used elsewhere
# get rid of one of these, pycurl_request is probably problematic

#FIXME: this is problematic: import pycurl_requests as req


# get rid of one of these too, keep subprocess if possible
import subprocess

import datetime
from pathlib import Path
#import requests FIXME: problem with this and urllib3
import webbrowser

from fastapi import UploadFile, File, Form
from fastapi import APIRouter, Query, HTTPException
#from fastapi.templating import Jinja2Templates
from starlette.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket

import os
import re
import memalib.mema_utility as mu

#FIXME: currently this is a hard install, look at https://github.com/amueller/word_cloud and stackoverflow for help
from wordcloud import WordCloud
import sqlite3
import logging

from configobj import ConfigObj

#load_dotenv()
#os.environ["'REPLICATE_API_TOKEN'"] = os.environ.get('REPLICATE_API_TOKEN')


config = ConfigObj('etc/mema.ini')

# this is a hack to make sure we have ENV everywhere we need it
my_env = mu.get_env(config['main']['env_file'])

logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)

con = sqlite3.connect(config['main']['db'], check_same_thread=False)
app = FastAPI(debug=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="static/media", html=True), name="media")   

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory="templates/en")

api_router = APIRouter()

#FIXME: Problems with xdg-open
os.environ["DISPLAY"] = ":0.0"

my_env = os.environ.copy()

#xset -display :0 -dpms

pi  = False 
# no test on system name in os now, unreliable, changed from arm to aaarch    
if config['main']['pi'] == 'yes' : 
    pi = True
        
@app.post("/")
async def info(info : Request):
    
    req_info = await info.json()
    
    #FIXME: parse raw input, need more for keywords
    raw_speech = req_info['input'] 
    intent     = req_info['intent']['intentName'] 
    
    #FIXME: parse numbers and courtesy, tidy this up
    number = None
    polite = None
    match = re.search(r'\b\d+\b', raw_speech)
    if match:
        number = match.group(0)     
    match     = re.search(r'\bplease\b', raw_speech)  
    if match:
        polite = match.group(0)  
    
    # confidence level too low or garbled intent
    if not len(intent) or (req_info['asrConfidence'] < float(config['main']['confidence'])) :
        mu.curl_speak(config['en_prompts']['not_understood'])
        return {
            "status" : "FAIL"
        }
        
    logging.debug(req_info)  
      
    # one or two, such as redirects can't be handled in the intent table
    if intent == "GetStory" and (number[0] in number):
        url = config['main']['intent_server'] + "/memory/" + str(number[0]) + "/speak"
        #print ('url is: ' + url)
        return RedirectResponse(url)    
    
    # intents are the options see: https://stackoverflow.com/questions/17881409/whats-an-alternative-to-if-elif-statements-in-python
    intents = {

        'TakePhoto'      : run_photo_command,
      #  'GetTime'        : run_time_command,
      #  'TellStory'      : print("tell story found"),   
      #  'Associate'      : print("associate photo and story found"),
        'RecordStory'    : run_record_command,
        'RecordVideo'    : run_video_command,
        'KillVideo'      : run_kill_video_command,  
        'LabelVideo'     : run_label_video_command,       
        'SlicePie'       : run_pie,
        'SearchPage'     : run_search_command,
        'LetsGo'         : fetch_privacy,
        'SearchMemories' : run_search_memories, 
        'Mosaic'         : run_mosaic_command     

    }
    
    if intent in intents:
        intents[intent](number,polite)
    else:
        mu.curl_speak(config['en_prompts']['nope'])

    logging.debug('--->is when this event was logged.')
    
    #FIXME: Not quite sure what purpose this serves?     
    return {
        "status" : "SUCCESS",
        "data" : req_info
    }
    
    logging.debug('<---is when this event returns.')

# take a photo and store it
            
def run_photo_command(number,please):
        
    # FIXME: nice to have websocket notification
    logging.debug('photo token' + my_env['REPLICATE_API_TOKEN'])
    result = ''
    try:
        result = subprocess.run(config['main']['picture_program'], check=True, text=True, capture_output=True, env=my_env).stdout
    except subprocess.CalledProcessError as e:
        logging.debug('picture command failed: ' + str(e.returncode) + ' ' + e.output)
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        
    (text, file_path) = result.split("|")
    file_path.rstrip()
    logging.debug('picture return' + ' ' + text + ' ' + file_path)
    
    unix_time = int(datetime.datetime.now().timestamp())
    description = text[0:30]
    
    cur = con.cursor()
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (text, text, file_path, unix_time, 0, 1, 'photo'))
    con.commit()    
    return 

# record audio and store it
    
def run_record_command(number,please):
    
    result = ''
    try:
        result = subprocess.run(config['main']['story_program'], check=True, text=True, capture_output=True).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    logging.debug('record story intial return' + ' ' + result)

    (text, file_path) = result.split('|')
    file_path.rstrip()
    logging.debug('record story return' + ' ' + text + ' ' + file_path)
    unix_time = int(datetime.datetime.now().timestamp())
    description = text[0:30]
    
    cur = con.cursor()
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (description, text, file_path, unix_time, 0, 1, 'text'))
    con.commit()
    return
    

  
def run_video_command(number,please):
    
    print("record video found") if config['main']['debug'] else None
    
    #result = subprocess.check_output(config['main']['video_program'], stderr=subprocess.DEVNULL)
    result = subprocess.check_output(config['main']['video_program'], stderr=subprocess.STDOUT)
    result_string = result.decode('utf-8')

    (text, media_path) = result_string.split('|')
    media_path.rstrip()
    unix_time = int(datetime.datetime.now().timestamp())
    description = text[0:30]   

    #FIXME: into multilingual parameters, later on
    description = 'unlabelled video'
    
    cur = con.cursor()
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (description, text, media_path, unix_time, 0, 1, 'video'))
    con.commit()
    return text      



#FIXME: ad-hoc remedy for non working VLC video on laptop
# bodge kill cvlc video process

def run_kill_video_command(number,please):
    
    print("kill video record found") if config['main']['debug'] else None
    
    com_array = config['main']['kill_video_command'].split()
    subprocess.call(com_array,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return


# FIXME: untested! shares code with transcribe and needs external AI, at present
# FIXME: label anything in database, extend this
   
def run_label_video_command(number,please):
    
    logging.debug("label video found " + str(number[0]))
    
    cur = con.cursor()
    result = cur.execute("SELECT * FROM memories WHERE memory_id=?",(number[0]))
    fields = result.fetchone()
    if fields is not None:
        if (fields[7] != 'video'):  # FIXME: label video and photos
            mu.curl_speak(config['en_prompts']['not_video'])
            return
        else:
            result = subprocess.run([config['main']['label_program'], number[0] ],  stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
            (text, file_path) = result.split('|')
            if (text != 'empty'):
                cur.execute("update memories set description = ? WHERE memory_id=?",(text, number[0]))
                con.commit()
            else:
                mu.curl_speak(config['en_prompts']['didnt_get'])
    else:
        mu.curl_speak(config['en_prompts']['sorry'])
    print(fields)
    return


#FIXME: to be done, associate n with m?
    
def run_associate_command(number,please):
    s2_out = subprocess.check_output([sys.executable, "/home/pi/projects/mema/associate.py"])
    return s2_out    
 

# produce a composite of thumbnails

def run_mosaic_command(number,please):
    mosaic_array = config['main']['mosaic_program'].split()
    subprocess.call(mosaic_array, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return
    
    
# skeletion get search page, see https://community.rhasspy.org/t/recognized-untrain-sentences-words/465/5
# discussion of wildcards

def run_search_command(number,please): 

    return

def run_pie(number,please):
    if please != None:
        mu.curl_speak(config['en_prompts']['what_kind'])
        mu.open_url(static/pie.html)
    else:
        mu.curl_speak(config['en_prompts']['say_please'])
    return

#FIXME: Oh boy, what a problem for something v. simple!
# make general!
    
def run_front_page(number,please):

    mu.curl_speak(config['en_prompts']['ok_going'])    
    mu.open_url('static/privacy.html')   
    return        


#FIXME: Probably merge this with memories fetch? Don't let these one page calls multiply?
@app.get("/privacy.html")
def fetch_privacy(request: Request, response_class=HTMLResponse ):
    mema_health = mu.system_health()
    if mema_health['wifi'] == 'dotgreen':
       mu.curl_speak('the_wifi_network_is_connected')
    else:
       mu.curl_speak('the_wifi_network_is_off')
    if config['main']['use_external_ai'] == 'yes':
       mu.curl_speak('external_services_for_labelling_and_transcription_are_on')
    else:
        mu.curl_speak('external_services_are_off')
    mu.open_url('static/privacy.html')   
 
def run_search_memories(number,please):
    print('in search memories')
    mu.curl_speak('found_a_set_of_memories')
    return    
      
#---------- screen only section

@app.get('/wordcloud')
async def get_wordcloud():
   return FileResponse('./static/wordcloud.svg')


# list of memories to screen    

@app.get("/memories.html")
def fetch_all(request: Request, response_class=HTMLResponse ):
    cur = con.cursor()
    # result = cur.execute("SELECT * FROM memories")
    result = cur.execute("select memory_id, description, file_path, strftime('%d-%m-%Y %H:%M', unix_time, 'unixepoch') as date, public, type from memories")
    results = result.fetchall()
    cur.close()
    #wordcloud() not here, in a cron
    return templates.TemplateResponse(
        "list.html",
        {"request": request, "results" :results, "mema_health": mu.system_health()}
    )


# get memory to screen

@app.get("/memory/{id}")
def fetch_data(request: Request, id: int):
    cur = con.cursor()
    result = cur.execute("SELECT * FROM memories WHERE memory_id={}".format(str(id)))
    field = result.fetchone()
    return templates.TemplateResponse(
        "memory.html",
        {"request": request,  "field": field}
    )

# ok ugly should be get, but problem with FastApi see: 
# https://stackoverflow.com/questions/62119138/how-to-do-a-post-redirect-get-prg-in-fastapi

@app.post("/memory/{id}/speak")
def fetch_data(id: int):
    
    #print("get story found") if config['main']['debug'] else None
    cur = con.cursor()
    result = cur.execute("SELECT text FROM memories WHERE memory_id={}".format(str(id)))
    fields = result.fetchone()
    if fields is not None:
        lines = fields[0].splitlines()
        text = ' '.join(lines)
        phrase = text.replace(' ','_')
        mu.curl_speak(phrase)
        url = 'memory' + '/' +str(id)
        mu.open_url(url)
    else:
        mu.curl_speak(config['en_prompts']['sorry'])
    return fields

# web socket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
    
