#!/usr/bin/env python3
from time import sleep
import subprocess

while True:
    cl = '''
curl -s --header "Content-Type: text/utf-8"   --request POST  \
--data 'hello_you_silly_billies'   http://localhost:12101/api/text-to-speech
'''
    cl_array = cl.split()
    subprocess.run(cl_array, check=True, capture_output=True).stdout
    sleep(5)

