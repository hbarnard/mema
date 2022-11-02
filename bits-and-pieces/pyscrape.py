#!/usr/bin/env python3

import pycurl
from io import BytesIO
buffer = BytesIO()
c = pycurl.Curl()
c.setopt(c.WRITEDATA, buffer)
c.setopt(pycurl.FAILONERROR, 0)

mema_servers = {

'intent_server':'http://10.0.0.76:8000',
'rhasspy_main':'http://10.0.0.76:12101',
'mimic3':'http://10.0.0.76:59125',
'node_red':'http://10.0.0.76:1880'

}

mema_health = {}

for name,url  in mema_servers.items():
    try:
        c.setopt(c.URL, url)
        c.perform()
        print(name + ' ' + 'Response Code: %d' % c.getinfo(c.RESPONSE_CODE))
        if (c.getinfo(c.RESPONSE_CODE) == 200):
            mema_health[name] = 'dotgreen'
        else:
            mema_health[name] = 'dotred'
    except:
        print(name + ' ' + 'no connection')
        mema_health[name] = 'dotred'

#Ending the session and freeing the resources
c.close()
