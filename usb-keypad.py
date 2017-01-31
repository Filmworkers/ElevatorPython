from evdev import InputDevice
from threading import Thread
from queue import Queue
from subprocess import call
from relays import Relay
import time

relay = Relay()
q = Queue()      

#Global variables
enteredCode = ""
intraKeyTime = 0
startTime = 0
keyCount = 0


def keyPadScan(out_q):
   DEVICE = "/dev/input/by-id/usb-Storm-Interface.com_Storm-Interface-event-kbd"
   dev = InputDevice(DEVICE)
   dev.grab()  #exclusive access

   keys = {
    2: "1",
    3: "2",
    4: "3",
    5: "4",
    6: "5",
    7: "6",
    8: "7",
    9: "8",
    10: "9",
    11: "Lock",
    30: "0",
    48: "Un-Lock"
    }

   for event in dev.read_loop():
       if event.type==1 and event.value==1:
         if event.code in keys:
             out_q.put([keys[event.code], event.sec])
               
def supervisor(in_q):
    global enteredCode
    global intraKeyTime
    global startTime
    global keyCount

    while True:
       if q.not_empty:
           keypress=in_q.get()
           key=keypress[0]  #Key the user hit
           timeStamp=keypress[1] #When the user hit the key
           keyCount+=1      #How many keys the user has hit
           if timeStamp-startTime > 5: #If it's been more than 5 seconds
              clear()             #start over
              intraKeyTime=timeStamp
              startTime=timeStamp
           if timeStamp-intraKeyTime < 3: #If user is confident
               enteredCode+=key      #append key
               intraKeyTime=timeStamp     #see how long it takes to get next key
           if keyCount==6: #User has entered the right number of keys
              if (key=="Un-Lock") | (key=="Lock"): #If last key hit was lock/unlock
                 if enteredCode=="031775Lock":
                    print("Third Floor Locked")
                    relay.OFF_3()
                    call(["omxplayer", "/home/pi/elevator/resource/Third lock.m4a"])
                    clear()
                 elif enteredCode=="031775Un-Lock":
                    print("Third Floor Un-Locked")
                    relay.ON_3()
                    call(["omxplayer", "/home/pi/elevator/resource/Third floor temp unlock.m4a"])
                    time.sleep(8)
                    relay.OFF_3()
                    call(["omxplayer", "/home/pi/elevator/resource/Third lock.m4a"])
                    clear()
                 elif enteredCode=="041775Lock":
                    relay.OFF_4()
                    print("Fourth Floor Locked")
                    call(["omxplayer", "/home/pi/elevator/resource/Penthouse lock.m4a"])
                    clear()
                 elif enteredCode=="041775Un-Lock":
                    print("Fourth Floor Un-Locked")
                    relay.ON_4()
                    call(["omxplayer", "/home/pi/elevator/resource/Penthouse temp unlock.m4a"])
                    time.sleep(8)
                    relay.OFF_4()
                    call(["omxplayer", "/home/pi/elevator/resource/Penthouse lock.m4a"])
                    clear()
                 elif enteredCode=="991775Un-Lock":
                    print("3&4 Un-Locked")
                    relay.ON_3()
                    relay.ON_4()
                    call(["omxplayer", "/home/pi/elevator/resource/Both unlock.m4a"])
                    clear()
                 elif enteredCode=="991775Lock":
                    print("3&4 Locked")
                    relay.OFF_3()
                    relay.OFF_4()
                    call(["omxplayer", "/home/pi/elevator/resource/Both lock.m4a"])
                    clear()
                 else: #wrong code entered
                    call(["omxplayer", "/home/pi/elevator/resource/Try again.m4a"])
                    clear()
                  
                  
           if keyCount>7: #User seems to be mashing keys willy nilly
              print("what")
              call(["omxplayer", "/home/pi/elevator/resource/You don't know the code.m4a"])
              clear()

           if (key=="Un-Lock") | (key=="Lock"):
              if (keyCount>3) & (keyCount<6):
                 call(["omxplayer", "/home/pi/elevator/resource/Meh.m4a"])
                 clear()
              
      
def clear():
   global enteredCode
   global keyCount
   global startTime
   global intraKeyTime
   enteredCode=""
   keyCount=0
   startTime=0
   intraKeyTime=0

keyPadScanThread = Thread(target=keyPadScan, args=(q,))
supervisorThread = Thread(target=supervisor, args=(q,))

supervisorThread.start()
keyPadScanThread.start()
