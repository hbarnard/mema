from fastapi import FastAPI, Request
import sys
import subprocess
import datetime

from fastapi import UploadFile, File, Form
from fastapi import APIRouter, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import sqlite3
from pathlib import Path


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
    
    # bit stupid since this is json, also switch maybe?
    if "story" in req_info:
        text = run_record_command()
        print("story found")
    elif "photo" in req_info:
        text = run_picture_command()
    elif "associate" in req_info:
        print("aasociate found")
    print(text)
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
    #return fields
    
'''    
@api_router.get("/", status_code=200)
def root(request: Request) -> dict:  # 2
    """
    Root GET
    """
    
    # 3
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "recipes": RECIPES},
    )
'''    
    
    
    
