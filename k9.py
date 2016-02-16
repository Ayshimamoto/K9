##K9 pseudo code
##-------------------------------------------------------------------------------
#!/usr/bin/env python

##Imports
import time
import cwiid
import time
import pygame
import pygame.mixer
import sys
import serial

##Setup Variables
buttons = 0
soundfilenames=[]
sounds=[]
filenametostring ={}
temp=[]
TXarray = [170, 85, 0, 127, 127, 0, 0, 0, 0]
sequence = 0
ser=serial.Serial('/dev/ttyAMA0', 9600, parity=serial.PARITY_NONE, timeout=0)
buttonlaststate = 0
buttonstate = 0
sequence = 0
txflags = 0
wiimotebuttons = 0
state = 0
PIDloop = 0
i = 0
wm = None
A='A'
B='B'
C='C'
channel = {A:0,B:0,C:0}
Wiictrl = {'One':False,'Two':False,'A':False,'B':False,'Minus':False,'Plus':False,'Home':False,'Fwd':False,'Rev':False,'Left':False,'Right':False,'C':False,'Z':False,'Last':0,'Current':0,'stick_x':127,'stick_y':127,'Mode':0,'acc_y':127,'continue':True,'homestate':0,'intlast':False}



def gettime():
     #this function returns the minutes and seconds of the system clock ad returns it
     from datetime import datetime
     onestep=datetime.now().strftime("%M%S")
     return(onestep)

def PIDservice(state):
     #this function puts the current minutes and seconds into the file /var/tmp/K9.PID.
     file=open('/var/tmp/K9.PID','w')
     value = str(gettime())
     value = value + state
     file.write(value) #as a string
     file.close()
     return(0)

def Writetolog(text):
     #This function will write a string into the log file /var/tmp/k9.log
     file=open('/var/tmp/k9.log','a')
     file.write(text) #write the line to the log
     file.close()
     return(0)


def a2s(arr):
        """array of integer byte values --> binary string
        """
        return ''.join(chr(b) for b in arr)

def soundinit():
	"""Initialize mixer and read Sound.txt into sounds[] 
	"""
	freq = 48000     # setup bitrate
	bitsize = -16    # unsigned 16 bit
	channels = 1     # 1 is mono, 2 is stereo
	buffer = 1024    # number of samples (experiment to get right sound)
	pygame.mixer.init(freq, bitsize, channels, buffer)
	file=open('/home/pi/K9/Sound.txt','r')
	basedir = '/home/pi/K9/'
	counta = 0
	for line in file:
	   if line <> '':
	      soundfilenames.append(line.rstrip('\n').split('|')) #splits the line at | and puts it into sounds
	      countb = 0
	      for i in range(len(soundfilenames[counta])):
                 print('counta ', counta,'i ',i, 'filename', soundfilenames[counta][i])
 	         filenametostring[soundfilenames[counta][i]] = ''
		 countb = countb + 1
	      counta = counta + 1
	file.close()
        for key in filenametostring:
           filenametostring[key] = pygame.mixer.Sound(basedir + key)
        print('process sound files')

        for line in range(len(soundfilenames)):
           temp = []
           for item in range(len(soundfilenames[line])):
                 temp.append(filenametostring[soundfilenames[line][item]])
           sounds.append(temp)

	channel['A'] = pygame.mixer.Channel(1)
	channel['B'] = pygame.mixer.Channel(2)
	channel['C'] = pygame.mixer.Channel(3)
	channel['A'].play(sounds[0][0])
	print(sounds[0][1])
	return channel[A]

def wiimoteinit(wm):
	"""intialize and connect to wiimote
	"""
        print 'Put Wiimote in discoverable mode now (press 1+2)...'
        global wiimote	
	i = 0
        while not wm:
	   try:
	      PIDservice('B') # update the PID service so DCP doesn't get angry.
	      wm=cwiid.Wiimote()
	   except RuntimeError:
	      print "Error opening wiimote connection"
	      print "attempt " + str(i)
	      i +=1
	      time.sleep(2)
	      
	print 'Wii Remote connected...'
        channel['A'].play(sounds[0][2])
 	print '\nPress the PLUS, Minus, 1 & 2 buttons to disconnect the Wii and end the application'
	time.sleep(.25)
	
	Rumble = False
	wm.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_ACC | cwiid.RPT_EXT
	return wm

def getbuttonstate(wm):
	"""periodic call to get data from wiimote and parse it into wii control dictionary
	"""
	# setting up constants to represent numeric values of buttons
	# this coorelates the button names with the values returned in software
	One = 2 # seriously, this wasn't my idea
	Two = 1 # WTF were they thinking
	A = 8 # This is in a function and independant from the same varaible in the main
        B = 4 
	Minus = 16
	Plus = 4096
	Home = 128
	Fwd = 2048
	Rev = 1024
	Left = 256
	Right = 512
	unknown1 = 32
	unknown2 = 64
	C = 2
	Z = 1

	# reset all buttons to false
	for item in Wiictrl:
	  if item not in ['Current','Last','stick_x','stick_y','state','acc_y','continue','homestate','intlast']:
	      Wiictrl[item] = False 
	temp = Wiictrl['Current']
 	Wiictrl['Last'] = temp

	Wiictrl['acc_y'] = wm.state['acc'][cwiid.Y]

	buttonstate = wm.state['buttons']
	nunchukbutton = 0
	Wiictrl['stick_x'] = 130
	Wiictrl['stick_y'] = 130
	if wm.state.has_key('nunchuk'):
	  nunchuk = wm.state['nunchuk']
	  nunchukbutton = nunchuk['buttons']
	  Wiictrl['stick_x'] = nunchuk['stick'][cwiid.X]
	  Wiictrl['stick_y'] = nunchuk['stick'][cwiid.Y]

	   #setup variable to see if anything important has changed
	Wiictrl['Current'] = buttonstate + nunchukbutton 

	if (buttonstate & One) > 0:
           Wiictrl['One']=True
	
	if (buttonstate & Two) >0:
	   Wiictrl['Two']=True

        if (buttonstate & A) >0:
           Wiictrl['A']=True

        if (buttonstate & B) >0:
           Wiictrl['B']=True

        if (buttonstate & Minus) >0:
           Wiictrl['Minus']=True

        if (buttonstate & Plus) >0:
           Wiictrl['Plus']=True

        if (buttonstate & Home) >0:
           Wiictrl['Home']=True

        if (buttonstate & Fwd) >0:
           Wiictrl['Fwd']=True

        if (buttonstate & Rev) >0:
           Wiictrl['Rev']=True

        if (buttonstate & Left) >0:
           Wiictrl['Left']=True

        if (buttonstate & Right) >0:
           Wiictrl['Right']=True
	
	if (nunchukbutton & C) >0:
	   Wiictrl['C']=True

        if (nunchukbutton & Z) >0:
           Wiictrl['Z']=True

        return False



def Parsebuttons(wiimotebuttons):
        """Decisions based on buttons
        """
        if Wiictrl['acc_y'] > 225:
           if (Wiictrl['intlast']==False):
		channel['C'].play(sounds[Wiictrl['homestate']+1][0])
	   Wiictrl['intlast']=True
	else:
	   Wiictrl['intlast']=False

	# put the previous states into local variables
	throttle = TXarray[3] 	
	turn = TXarray[4]
	wiimotebuttons = TXarray[5] 
	nunchuckbuttons = TXarray[6]

        # if buttons changed then events will need to trigger
        if (Wiictrl['Current'] != Wiictrl['Last']):
	   wiimotebuttons = 128 #rebuild wiimote buttons
	   nunchuckbuttons = 192  + Wiictrl['homestate'] # rebuild nunchuck buttons
           if (Wiictrl['A']):
                print 'A button pressed \n'
                if wm.state['acc'][cwiid.Y] < 110:
                        channel['A'].play(sounds[Wiictrl['homestate']+1][1])
                elif wm.state['acc'][cwiid.Y] > 125:
                        channel['C'].play(sounds[Wiictrl['homestate']+1][3])
                else:
                        channel['A'].play(sounds[Wiictrl['homestate']+1][2])
                print 'Acc: x=%d y=%d z=%d ' % (wm.state['acc'][cwiid.X],
                                               wm.state['acc'][cwiid.Y],
                                               wm.state['acc'][cwiid.Z])
                print 'Stick: x=%d y=%d \n' % (Wiictrl['stick_x'],Wiictrl['stick_y'])

                wiimotebuttons = wiimotebuttons + 32 
	
           if (Wiictrl['B']):
                print 'B button pressed \n'
                if wm.state['acc'][cwiid.Y] < 110:
                        channel['B'].play(sounds[Wiictrl['homestate']+1][4])
                elif wm.state['acc'][cwiid.Y] > 125:
                        channel['C'].play(sounds[Wiictrl['homestate']+1][6])
                else:
                        channel['B'].play(sounds[Wiictrl['homestate']+1][5])
                print 'Acc: x=%d y=%d z=%d' % (wm.state['acc'][cwiid.X],
                                               wm.state['acc'][cwiid.Y],
                                               wm.state['acc'][cwiid.Z])
                wiimotebuttons = wiimotebuttons + 64

	   if (Wiictrl['One']):
		print 'One button pressed \n'
		wiimotebuttons = wiimotebuttons + 1

           if (Wiictrl['Two']):
                print 'Two button pressed \n'
                wiimotebuttons = wiimotebuttons + 2

           if (Wiictrl['Plus']):
                print 'Plus button pressed \n'
                wiimotebuttons = wiimotebuttons + 4

           if (Wiictrl['Home']):
                print 'Home button pressed \n'
                wiimotebuttons = wiimotebuttons + 8
                Wiictrl['homestate'] = Wiictrl['homestate'] + 1
                if Wiictrl['homestate'] > 3:
                   Wiictrl['homestate'] = 0
                #   nunchuckbuttons = nunchuckbuttons + Wiictrl['homestate']
		
                if Wiictrl['homestate'] == 0:
                   wm.led = 0
                if Wiictrl['homestate'] == 1:
                   wm.led = 1
                if Wiictrl['homestate'] == 2:
                   wm.led = 2
                if Wiictrl['homestate'] == 3:
                   wm.led = 3
                if Wiictrl['homestate'] == 4:
                   wm.led = 4
                if Wiictrl['homestate'] == 5:
                   wm.led = 5
                if Wiictrl['homestate'] == 6:
                   wm.led = 6
                if Wiictrl['homestate'] == 7:
                   wm.led = 7
                if Wiictrl['homestate'] == 8:
                   wm.led = 8

		print 'homestate = %d' % (Wiictrl['homestate'])


           if (Wiictrl['Minus']):
                print 'Minus button pressed \n'
                wiimotebuttons = wiimotebuttons + 16

           if (Wiictrl['Fwd']):
                print 'Fwd button pressed \n'
		#throttle = throttle + 64

           if (Wiictrl['Rev']):
                print 'Rev button pressed \n'
		#throttle = throttle - 64

           if (Wiictrl['Left']):
                print 'Left button pressed \n'
		#turn = turn - 64

           if (Wiictrl['Right']):
                print 'Right button pressed \n'
		#turn = turn + 64

	   if (Wiictrl['C']):
		print 'C button pressed \n'
		nunchuckbuttons + 16	  
	   
           if (Wiictrl['Z']):    
                print 'Z button pressed \n'
                nunchuckbuttons + 32

	   if (Wiictrl['Plus'] and Wiictrl['Minus'] and Wiictrl['One'] and Wiictrl['Two']):
		print 'Exiting program \n'
		Wiictrl['continue']=False

	if (wm.state['error'] > 0):
	  print 'error = %d \n' % (wm.state['error'])

	#All throttle control here
	throttle = 127 #start from scratch each program pass
	#y fwd = 227     /     y rev = 34

	if (Wiictrl['stick_y'] > 140):
		throttle = throttle + Wiictrl['stick_y'] - 140
	if (Wiictrl['stick_y'] < 120):
		throttle = throttle - ( 120 - Wiictrl['stick_y'])
        if (Wiictrl['Fwd']):
                throttle = throttle + 32
	if (Wiictrl['Rev']):
		throttle = throttle - 32
	if (throttle > 255):
		throttle = 255
  	if (throttle < 1):
		throttle = 0

	#All turn control here
	turn = 127 # start from scratch
	#x left = 31     /    x right = 220

        if (Wiictrl['stick_x'] > 140):
                turn = turn + (Wiictrl['stick_x'] - 140)
        if (Wiictrl['stick_x'] < 120):
                turn = turn - ( 120 - Wiictrl['stick_x'])
        if (Wiictrl['Left']):
                turn = turn - 32
        if (Wiictrl['Right']):
                turn = turn + 32
	if (turn > 255):
		turn = 255
	if (turn < 1):
		turn = 0

	
   	TXarray[3] = 255 & (throttle)               #set in parsebuttons
   	TXarray[4] = 255 & (turn)                   #set in parsebuttons
   	TXarray[5] = 255 & (wiimotebuttons)         #set in parsebuttons
   	TXarray[6] = 255 & (nunchuckbuttons)        #set in parsebuttons



	return wiimotebuttons

	

	
##Initialization

#update PID so DCP knows this program is running
PIDservice('B') # state 'B' instructs DCP this is looking for wiimote

   ##load sounds & setup mixer
channelA=soundinit()
#channel['A'].play(sounds[0][1])
print(sounds[0][1])

wm = wiimoteinit(wm)

   ##setup initial wiimote state (rumble = False)
   ##Main Program loop
while Wiictrl['continue']:
   ##   get button state
   getbuttonstate(wm)

   ##   parse button results into dictionary & setup control variables
   buttons = Parsebuttons(buttons)

   ##   transmit frame out serial port
   sequence = sequence + 1
   #TXarray[0] = 170
   #TXarray[1] = 85
   TXarray[2] = 255 & (sequence)
   #TXarray[3] = 255 & (throttle)  		#set in parsebuttons
   #TXarray[4] = 255 & (turn) 			#set in parsebuttons
   #TXarray[5] = 255 & (wiimotebuttons) 	#set in parsebuttons
   #TXarray[6] = 255 & (nunchuckbuttons) 	#set in parsebuttons
   #TXarray[7] = 255 & (txflags)
   TXarray[8] = 255 & (TXarray[2] + TXarray[3] + TXarray[4] + TXarray[5] + TXarray[6] + TXarray[7])
   
   TXstring = a2s(TXarray)
   ser.open()
   ser.write(TXstring),    #echo message on screen
   response = ser.read()
   # print(response),
   ser.close()


   ##   Process RX frames   
   
   
   ##   every 2 seconds output summary of status to log file

   ##   every 30 seconds update /var/tmp/K9.PID
   PIDloop = PIDloop + 1
   if (PIDloop > 428):
	PIDloop = 0
	PIDservice('C') # 'C' tells DCP we are in the main loop


   ## loop every 70ms
   time.sleep(.07)

PIDservice('Z') # 'Z' tells DCP we intentionally exited
time.sleep(1) # give it a moment to rest before the final exit don't want to write too frequently
sequence = 0
while (pygame.mixer.get_busy()) and (sequence <120):
   time.sleep(.5)
   sequence = sequence + 1
PIDservice('Z') # 'Z' tells DCP we intentionally exited
sys.exit(0)
