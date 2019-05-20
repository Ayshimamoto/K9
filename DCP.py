#!/usr/bin/env python
#-------------------------------------------------------------------------------


import time
import os, errno
import subprocess, signal
PIDFile = '/var/tmp/K9.PID'
StartK9 = '/usr/bin/python /home/pi/K9/k9.py &'

WDT = 30
def gettime():
     #this function returns the minutes and seconds of the system clock ad returns it
     from datetime import datetime
     onestep=datetime.now().strftime("%M%S")
     return(onestep)

def PIDservice():
     #this function reads the minutes and seconds out of the file /var/tmp/K9.PID.
     try:
	file=open(PIDFile,'r')
     	value = file.readline() #as a string
     	file.close()
     except:
        print "whoops"
	value = "0000A"
     return(value)

value = (gettime())
print "time"
print value
filetime = str(PIDservice())
print "file"
print filetime
currenttime = int(value)
currentminute = int(value[1]) + int(value[0])*10
currentseconds = int(value[3]) + int(value[2])*10
fileminute = int(filetime[1]) + int(filetime[0])*10
fileseconds = int(filetime[3]) + int(filetime[2])*10


#status A = Started by DCP, B = Searching for Wiimote, C = steady state, 

Status = filetime[4]
if Status == 'A': # 'A' represents if DCP started K9.py 
        WDT = int(60)
if Status == 'B': # 'B' represents if it is searching for the Wiimote
        WDT = int(60)
if Status == 'C': # 'C' represents if everything is in steady state
        WDT = int(30)
if Status == 'D': # 'D' represents entering park and bark mode with extended loading times
	WDT = int(120)

print('current time ', currenttime, currentminute, currentseconds)
print('file time', filetime, fileminute, fileseconds)
differenceminute = (currentminute - fileminute) 
differenceseconds = (currentseconds - fileseconds)
difference = differenceminute*60 + differenceseconds
print('difference', difference)
TDW = WDT - 3600
if ((difference > WDT) and (difference < 3600 )) or ((difference > TDW) and (difference <-1)):
    print("reset suggested",differenceminute, differenceseconds)

    # End any existing K9 process
    p = subprocess.Popen(['ps', 'x'], stdout=subprocess.PIPE)
    out, err = p.communicate()

    for line in out.splitlines():
        if 'k9.py' in line:
                pid = int(line.split(' ',2)[1])
                os.kill(pid, signal.SIGKILL)
    time.sleep(0.2);
    # start a new process
    os.system(StartK9)
