#!/usr/bin/env python3
from time import sleep
import subprocess
my_data = "hello".encode(errors='ignore')

cl = '''curl -s --header "Content-Type: text/utf-8"   --request POST  --data 'hello_you_sillies'   http://localhost:12101/api/text-to-speech'''
cl_array = cl.split()
print(cl_array)
subprocess.run(cl_array, check=True, capture_output=True).stdout

exit()

while True:
    print("hello you sillies")
    sleep(5)

exit()
