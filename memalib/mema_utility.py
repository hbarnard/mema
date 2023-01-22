# utility functions, some of which will be deprecated
import threading as th
from io import BytesIO
import pycurl
import logging
import subprocess
from pathlib import Path
import re
import datetime
from configobj import ConfigObj
from fastapi import WebSocket

import sqlite3

config = ConfigObj('etc/mema.ini')
logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)


# separate out, need for both face unlock and direct path
def declare_mema_health():
    mema_health = system_health()
    if mema_health['wifi'] == 'dotgreen':
       curl_speak('the_wifi_network_is_connected')
    else:
       curl_speak('the_wifi_network_is_off')
    if config['main']['use_external_ai'] == 'yes':
       curl_speak('external_services_for_labels_and_transcription_are_on')
    else:
        curl_speak('external_services_are_off')

# separate from unlock, since we want to sign in the guest user too
# without going through the face_unlock    
def database_sign_in(first_name,last_name):
    con = sqlite3.connect(config['main']['db'], check_same_thread=False)
    unix_time = int(datetime.datetime.now().timestamp())
    # remove any previous or 'zombie' sign ins
    cur = con.cursor()   
    cur.execute(("update contacts set logon = ? where logon >= ?"),(None,0))
    #FIXME: sign in named holder, can be guest, what to do if not found?
    result = cur.execute(("update contacts set logon = ? where first_name = ? and last_name = ?"),(unix_time,first_name,last_name))
    users = cur.execute("select * from contacts where logon > 0")
    user = users.fetchone()
    cur.close()
    con.commit()
    con.close()
    return user
    
    
def get_current_user():
    con = sqlite3.connect(config['main']['db'], check_same_thread=False)
    cur = con.cursor()    
    users = cur.execute("select * from contacts where logon > 0")
    # do this
    user = users.fetchone()
    cur.close()
    con.close()
    return user        


def run_sign_out(number,please):
    con = sqlite3.connect(config['main']['db'], check_same_thread=False)
    curl_speak('thank_you_signing_out_now')
    unix_time = int(datetime.datetime.now().timestamp())
    cur = con.cursor()
    result = cur.execute(("update contacts set logon = ? where logon >= ?"),(None,0))
    cur.close()
    con.commit()
    con.close()
    return


def open_url(page):
    try:
        url = config['main']['intent_server'] + '/' + page
        open_command = r'jaro  {}'.format(url)
        subprocess.Popen(open_command,shell = True)   
    except subprocess.CalledProcessError as e:
        logging.debug('jaro open_url command error' + open_command)
        raise RuntimeError("command '{}' return here with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    return        


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


# spoken prompts without going back into node red, prompts are word_word_word in mema.ini

def curl_speak(phrase):
    logging.debug(phrase)
    cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data '{speech}'   http://localhost:12101/api/text-to-speech > /dev/null'''.format(speech = phrase)
    cl_array = cl.split()
    subprocess.call(cl_array,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return


def curl_get(url):
    logging.debug(url)
    cl = '''curl -s {url}'''
    cl_array = cl.split()
    subprocess.call(cl_array,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return


#FIXME: this is a hack, mainly to get the REPLICATE_API_KEY reliably in various scripts and subprocesses
# the actual location of .env is a configuration parameter in mema.ini
def get_env(env_file):
    my_env = {}

    with open(env_file, 'r') as f:
        for line in f:
            items = line.split('=')
            key, value = items[0], items[1].rstrip()
            my_env[key] = value
    return my_env

#FIXME: this may requite a no password entry via root visudo, see: 
# https://stackoverflow.com/questions/567542/running-a-command-as-a-super-user-from-a-python-script

def docker_control(command,instance_name):
    try:
        subprocess.run(['sudo' , "docker", command, instance_name], check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    # make a file name from the current unix timestamp
    return int(datetime.datetime.now().timestamp())


#FIXME: not used currently, but useful

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
    
    # test whether wifi is up, make a long line rather than use complex regex!
    t = Path('/proc/net/wireless').read_text()
    t = ''.join(t.splitlines())
    m = re.search(r'wlp', t)
    #print('m is ', m, t)  
    if m:
        mema_health['wifi'] = 'dotgreen'
    else:
        mema_health['wifi'] = 'dotred'
    return mema_health


def timer_function():  
   print("timed out \n")  
   

# websocket manager, inspiration is https://gealber.com/simple-chat-app-websockets-fastapi   
   
class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    async def broadcast(self, data: str):
        for connection in self.connections:
            await connection.send_text(data)

