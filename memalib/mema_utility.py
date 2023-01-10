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

config = ConfigObj('etc/mema.ini')
logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)

'''
#FIXME: is this used anywhere right now?
class run_subprocess(th.Thread):
    def __init__(self,command):
        self.stdout = None
        self.stderr = None
        th.Thread.__init__(self)
        self.command = command

    def run(self):
        p = subprocess.call(self.command, shell=True)
        #self.stdout, self.stderr = p.communicate()
 
#FIXME: Probably don't need this either?    
def demote(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)
    return result
'''

def open_url(page):
    try:
        url = config['main']['intent_server'] + '/' + page
        open_command = r'jaro  {}'.format(url)
        logging.debug('in jaro command ' + open_command)
        #open_command = 'chromium-browser --display=:0 --kiosk --incognito --window-position=0,0 https://reelyactive.github.io/diy/pi-kiosk/'
        #subprocess.run([open_command, number[0] ],  stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        #subprocess.run(open_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            #logging.debug(items)
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

