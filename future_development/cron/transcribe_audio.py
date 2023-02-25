#!/usr/bin/env python3

import sqlite3
import logging
import os
from configobj import ConfigObj

# since this will be a cron, full paths are necessary in the script!
# transcribe audio where currently untranscribed

def transcribe(con):
    # collect untranscribed audio
    cur = con.cursor()
    res = cur.execute("select rowid, description, text, file_path, type from memories where description like '%unlabelled%' and type = 'rec'")
    results = res.fetchall()
    cur.close()

    for result in results:
        transcribe_command = config['main']['transcribe_program'] + ' ' + results[2] +  ' > /tmp/transcription'
        log.debug('transcribe command is ' + transcribe_command)
        log.debug('result is ' + result)
        subprocess.call(transcribe_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open('/tmp/transcription') as trans: f = trans.read()
        description = f[:30]
        # update
        cur.execute('''UPDATE memories SET description = ?, text = ? WHERE id = ?''', (description, f, result[0]))
        con.commit()
        # remove temp file
        os.remove('/tmp/transcription')

def main():
    root_dir = '/home/pi/mema/'
    config = ConfigObj(root_dir + 'etc/mema.ini')
    logging.basicConfig(filename=(root_dir + config['main']['logfile_name']), format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)
    
    con = sqlite3.connect(config['main']['db'], check_same_thread=False)
    transcribe(con)
    
if __name__ == '__main__':
    main()

    
