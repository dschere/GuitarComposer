""" 
Find a free tcp port number
"""
import sys
import os
import time

START_PORT_RANGE = 2000
END_PORT_RANGE = 10000
MAX_TCP_LINGER_AGE = 300 

_used_ports = set()


def _linux_find_free_tcp_port():
    global _used_ports

    output = os.popen("netstat -tnlup 2> /dev/null","r").readlines()
    for i in range(2,len(output)):
        text = output[i].split()[3].split(':')[1]
        if len(text) > 0:
            _used_ports.add( int(text) )
    for port in range(START_PORT_RANGE,END_PORT_RANGE):
        if port not in _used_ports:
            tfile = "/tmp/%d-tcp-port" % port
            if os.access(tfile,os.F_OK):
                now = time.time()
                age = now - os.stat(tfile).st_mtime
                if age < MAX_TCP_LINGER_AGE:
                    continue     
            _used_ports.add(port)
            open(tfile,"w").write("")
            return port
        
    raise RuntimeError("Unable to find an unused TCP port number!")    

        

def find_free_tcp_port():
    if sys.platform == 'linux':
        return _linux_find_free_tcp_port()
    raise RuntimeError("Unsupported platform")
