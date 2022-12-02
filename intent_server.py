from fastapi import FastAPI, Request
import sys
import os, pwd

# for system health, but pycurl should be used elsewhere
# get rid of one of these, pycurl_request is probably problematic
import pycurl
#FIXME: this is problematic: import pycurl_requests as req
from io import BytesIO

# get rid of one of these too, keep subprocess if possible
import subprocess
#from plumbum import FG, BG, local
import threading as th

import datetime
from pathlib import Path
#import requests FIXME: problem with this and urllib3
import webbrowser

from fastapi import UploadFile, File, Form
from fastapi import APIRouter, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket

import re

#FIXME: currently this is a hard install, look at https://github.com/amueller/word_cloud and stackoverflow for help
from wordcloud import WordCloud

import sqlite3
import configparser

#FIXME: ConfigObj needs to be used everywhere
from configobj import ConfigObj

class run_subprocess(th.Thread):
    def __init__(self,command):
        self.stdout = None
        self.stderr = None
        th.Thread.__init__(self)
        self.command = command

    def run(self):
        p = subprocess.call(self.command, shell=True)
        #self.stdout, self.stderr = p.communicate()
 
#FIXME: Probably don't need this?
    
def demote(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)
    return result                


#FIXME: Need this for xdg-open, maybe theres another simpler way?
# see also: https://stackoverflow.com/questions/61302291/python-subprocess-popen-execute-as-different-user v, similar
        
def exec_cmd(username,command):
    # get user info from username
    pw_record = pwd.getpwnam(username)
    homedir = pw_record.pw_dir
    user_uid = pw_record.pw_uid
    user_gid = pw_record.pw_gid
    env = os.environ.copy()
    env.update({'HOME': homedir, 'LOGNAME': username, 'PWD': os.getcwd(), 'FOO': 'bar', 'USER': username})

    # execute the command
    proc = subprocess.Popen([command],
                              shell=True,
                              env=env,
                              preexec_fn=demote(user_uid, user_gid),
                              stdout=subprocess.PIPE)
    return


#FIXME: spoken prompts without going back into node red
# two formats used for speech and rhasspy api can be used directly, this is a bodge
def curl_speak(phrase):
    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech > /dev/null'''.format(speech = phrase)
    cl_array = cl.split()
    subprocess.call(cl_array,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return

#FIXME: this needs to be elsewhere but 'for the moment'

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
    
    # test whether wifi is up
    text_string = Path('/proc/net/wireless').read_text()
    m = re.match(r"wlp2s0", text_string)
    if m:
        mema_health['wifi'] = 'dotgreen'
    else:
        mema_health['wifi'] = 'dotred'
    return mema_health

def timer_function():  
   print("timed out \n")  

config = ConfigObj('etc/mema.ini')
#config.read('etc/mema.ini')

con = sqlite3.connect(config['main']['db'], check_same_thread=False)

app = FastAPI(debug=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="static/media", html=True), name="media")   


BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates"))

api_router = APIRouter()

os.environ["DISPLAY"] = ":0.0"

# convenience for separating Pi and a random laptop
pi = False
if os.uname()[4].startswith("arm"): 
    pi = True 

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
        curl_speak(config['en_prompts']['not_understood'])
        return {
            "status" : "FAIL"
        }
        
    print(req_info) if config['main']['debug'] else None  
      
    # one or two, such as redirects can't be handled in the intent table
    if intent == "GetStory" and (number[0] in number):
        url = config['main']['intent_server'] + "/memory/" + str(number[0]) + "/speak"
        #print ('url is: ' + url)
        return RedirectResponse(url)    
    
    # intents are the options see: https://stackoverflow.com/questions/17881409/whats-an-alternative-to-if-elif-statements-in-python

 
    intents = {

        'TakePhoto'      : run_photo_command,
     #  'TellStory'      : print("tell story found"),   
    #   'Associate'      : print("associate photo and story found"),
        'RecordStory'    : run_record_command,
        'RecordVideo'    : run_video_command,
        'KillVideo'      : run_kill_video_command,  
        'LabelVideo'     : run_label_video_command,       
        'SlicePie'       : run_pie,
        'SearchPage'     : run_search_command,
        'LetsGo'         : run_front_page,
        'SearchMemories' : run_search_memories      

    }
    
    if intent in intents:
        intents[intent](number,polite)
    else:
        curl_speak(config['en_prompts']['nope'])

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
    #command = config['main']['xdg_open_command'] + '?type=thinking'
    #xdg_open_array = command.split()
    # subprocess.call(xdg_open_array, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cur = con.cursor()
    picture = local[config['main']['picture_program']]
    result = picture()
    (text, file_path) = result.split('|')
    file_path.rstrip()
    unix_time = int(datetime.datetime.now().timestamp())
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (text, text, file_path, unix_time, 0, 1, 'photo'))
    con.commit()
    print("photo command done") if config['main']['debug'] else None
    return 

# record audio and store it
    
def run_record_command(number,please):
    
    print("record story found") if config['main']['debug'] else None
    s = th.Timer(30, timer_function) 
    s.start() 
     
    result = subprocess.check_output(config['main']['story_program'])
    result_string = result.decode('utf-8')

    (text, file_path) = result_string.split('|')
    file_path.rstrip()
    unix_time = int(datetime.datetime.now().timestamp())
    description = text[0:30]
    
    cur = con.cursor()
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (description, text, file_path, unix_time, 0, 1, 'text'))
    con.commit()
    return text  
    
#FIXME: vlc doesn't work properly on laptop  
# record video and store it
  
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


#FIXME: to be done
    
def run_associate_command(number,please):
    print("running classifier") if config['main']['debug'] else None
    s2_out = subprocess.check_output([sys.executable, "/home/pi/projects/mema/associate.py"])
    return s2_out    
 

# skeletion get search page, see https://community.rhasspy.org/t/recognized-untrain-sentences-words/465/5
# discussion of wildcards

def run_search_command(number,please): 

    return

def run_pie(number,please):
    if please != None:
        curl_speak(config['en_prompts']['what_kind'])
        Call_URL = "http://localhost:8000/static/pie.html"
        mycmd = r'handlr open  {}'.format(Call_URL)
        subprocess.Popen(mycmd,shell = True) 
    else:
        curl_speak(config['en_prompts']['nope'])
        return

#FIXME: Oh boy, what a problem for something v. simple!
# make general!

def run_front_page(number,please):

    Call_URL = "http://localhost:8000/memories.html"
    mycmd = r'handlr open  {}'.format(Call_URL)
    subprocess.Popen(mycmd,shell = True) 
 

def run_search_memories(number,please):
    print('in search memories')
    curl_speak('found_a_set_of_memories')
    return    
      
#---------- screen only section

@app.get('/wordcloud')
async def get_wordcloud():
   return FileResponse('./static/wordcloud.svg')


# list of memories to screen    

@app.get("/memories.html")
def fetch_all(request: Request):
    cur = con.cursor()
    # result = cur.execute("SELECT * FROM memories")
    result = cur.execute("select memory_id, description, file_path, strftime('%d-%m-%Y %H:%M', unix_time, 'unixepoch') as date, public, type from memories")
    results = result.fetchall()
    cur.close()
    #wordcloud() not here, in a cron
    return TEMPLATES.TemplateResponse(
        "list.html",
        {"request": request, "results" :results, "mema_health": system_health()}
    )


# get memory to screen

@app.get("/memory/{id}")
def fetch_data(request: Request, id: int):
    
    cur = con.cursor()
    result = cur.execute("SELECT * FROM memories WHERE memory_id={}".format(str(id)))
    field = result.fetchone()
    return TEMPLATES.TemplateResponse(
        "memory.html",
        {"request": request,  "field": field}
    )

# ok ugly should be get, but problem with FastApi see: 
# https://stackoverflow.com/questions/62119138/how-to-do-a-post-redirect-get-prg-in-fastapi

@app.post("/memory/{id}/speak")
def fetch_data(id: int):
    
    print("get story found") if config['main']['debug'] else None
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

# web socket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        if websocket.connected:
            data = await websocket.receive_text()
            await websocket.send_text(f"message text")
    
    
