from fastapi import FastAPI, Request
import sys
import subprocess
import datetime
import requests

from fastapi import UploadFile, File, Form
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import re

import sqlite3
from pathlib import Path


# spoken prompts without going back into node-red

def curl_speak(phrase):

    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech'''.format(speech = phrase)
    cl_array = cl.split()
    #print(cl_array)
    subprocess.run(cl_array, check=True, capture_output=True).stdout
    return

'''
Improvements, parameter file for file paths, program paths
some logging, some listing for database contents
'''

con = sqlite3.connect("/var/spool/mema/db/memories.db", check_same_thread=False)

app = FastAPI(debug=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates"))

api_router = APIRouter()



@app.post("/")
async def getInformation(info : Request):
    
    req_info = await info.json()
    intent = req_info['intent']['intentName']
    raw_speech = req_info['input']
    print(req_info)
    
    if intent == "TakePhoto":
        print("take photo found")
        #run_picture_command()
    elif intent == "GetStory":
        #fetch_data(id: int)
        print("get story found")
        story_number = re.findall(r'\b\d+\b', raw_speech)
        print(story_number[0])
        url = "http://localhost:8000/memory/" + str(story_number[0]) + "/speak"
        print('url is ' + url)
        return RedirectResponse(url)
    elif intent == "TellStory":
        print("tell story found")    
    elif intent == "Associate":
        print("associate photo and story found")
    elif intent == "StoreStory":
        #run_record_command()
        print("record story found")
    else:
        print("nothing found")
    
    return {
        "status" : "SUCCESS",
        "data" : req_info
    }


# ok this needs optimising, doesn't it?
    
def run_picture_command():
    cur = con.cursor()
    result = subprocess.run(["/home/pi/projects/mema/picture.py"], check=True, capture_output=True, text=True).stdout
    (text, file_path) = result.split('|')

    unix_time = int(datetime.datetime.now().timestamp())
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (text, text, file_path, unix_time, 0, 1, 'photo'))
    con.commit()
    return text
    
def run_record_command():
    result = subprocess.run(["/home/pi/projects/mema/record_story.py"], check=True, capture_output=True, text=True).stdout
    (text, file_path) = result.split('|')
    
    unix_time = int(datetime.datetime.now().timestamp())
    description = text[0:30]
    
    cur = con.cursor()
    cur.execute("INSERT INTO memories (description, text, file_path, unix_time, public, owner, type) values (?, ?,?, ?, ?, ?,? )", (description, text, file_path, unix_time, 0, 1, 'text'))
    con.commit()
    return text  
    
def run_associate_command():
    print("running classifier")
    s2_out = subprocess.check_output([sys.executable, "/home/pi/projects/mema/associate.py"])
    return s2_out    
    
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
    result = cur.execute("SELECT * FROM memories")
    results = result.fetchall()
    return TEMPLATES.TemplateResponse(
        "list.html",
        {"request": request, "results" :results}
    )


# ok ugly should be get, but problem with FastApi see: 
# https://stackoverflow.com/questions/62119138/how-to-do-a-post-redirect-get-prg-in-fastapi
@app.post("/memory/{id}/speak")
def fetch_data(id: int):
    cur = con.cursor()
    result = cur.execute("SELECT text FROM memories WHERE memory_id={}".format(str(id)))
    fields = result.fetchone()
    if fields is not None:
        print(fields)
        phrase = fields[0].replace(' ','_')
        curl_speak(phrase)
    else:
        curl_speak("I_cannot_find_that_sorry")
    return fields


        
    
    
