import configparser
#from influxdb import InfluxDBClient
import time
from evdev import InputDevice
from threading import Thread
from queue import Queue
from subprocess import call
import schedule
from relays import Relay

relay = Relay()
threadQueue = Queue()
relockQueue = Queue()

configFile = configparser.ConfigParser()
configFile.read('/home/pi/elevator/ElevatorPython/ElevatorConfig.txt')
config = configFile['Configuration']
            
#Global variables
enteredCode = ""
timeStamp = 0
intraKeyTime = 0
startTime = 0
keyCount = 0
masterUnlock = False
goodCode = True


def keyPadScan():
   DEVICE = "/dev/input/by-id/usb-Storm-Interface.com_Storm-Interface-event-kbd"
   dev = InputDevice(DEVICE)
   dev.grab()  #exclusive access, Linux won't think it's a keyboard

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
            threadQueue.put([keys[event.code], event.sec]) #drop keypress on the Queue

def relock():
   while True:
      if relockQueue.not_empty:
         floor = relockQueue.get()
         if floor == 3:
            time.sleep(8)
            lockFloor3()
         if floor == 4:
            time.sleep(8)
            lockPenthouse()

   
def lockFloor3():             
    relay.OFF_3()
    call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Third lock.m4a"])
    report("Third Floor Locked")
    clear()

def lockPenthouse():
    relay.OFF_4()
    call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Penthouse lock.m4a"])
    report("Fourth Floor Locked")
    clear()
    
def tempUnlockFloor3():
    relay.ON_3()
    if masterUnlock:
       call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Third unlock.m4a"])
       report("Third Floor Un-Lock")
    else:
       report("Third floor Temp Un-locked")
       call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Third floor temp unlock.m4a"])
       relockQueue.put(3)
    clear()

def tempUnlockPenthouse():
    relay.ON_4()
    if masterUnlock:
       call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Penthouse unlock.m4a"])
       report("Fourth Floor Un-Lock")
    else:
       report("Fourth Floor Temp Un-Locked")
       call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Penthouse temp unlock.m4a"])
       relockQueue.put(4)
    clear()

def timer():
    global timeStamp
    global goodCode
    while True:
        time.sleep(1)
        if int(time.time() - timeStamp > 3):
            if not goodCode:
                print("try again")
                call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Try again.m4a"])
                goodCode = True
   
def supervisor():
    global enteredCode
    global intraKeyTime
    global startTime
    global keyCount
    global masterUnlock
    global timeStamp
    global goodCode

    while True:
       if threadQueue.not_empty:
           keypress = threadQueue.get()
           goodCode = False
           key = keypress[0]  #Key the user hit
           timeStamp = keypress[1] #When the user hit the key
           keyCount += 1      #How many keys the user has hit
           if timeStamp - startTime > 5: #If it's been more than 5 seconds
              clear()             #start over
              intraKeyTime = timeStamp
              startTime = timeStamp
           if timeStamp - intraKeyTime < 3: #If user is confident
              enteredCode += key      #append key
              intraKeyTime = timeStamp     #see how long it takes to get next key
              
           if keyCount == 3:
               if enteredCode == config["ShortFloor3Code"]:
                  goodCode = True
                  tempUnlockFloor3()
                  clear()
               elif enteredCode == config["ShortFloor4Code"]:
                  goodCode = True
                  tempUnlockPenthouse()
                  clear()
               elif enteredCode == config["FreelanceFloor3Code"]:
                  goodCode = True
                  tempUnlockFloor3()
                  clear()
               elif enteredCode == config["FreelanceFloor4Code"]:
                  goodCode = True
                  tempUnlockPenthouse()
                  clear()
               
           if keyCount == 6: #User has entered the right number of keys
              if (key == "Un-Lock") | (key == "Lock"): #If last key hit was lock/unlock
                 # Lock Third Floor
                 if enteredCode == config["ThirdFloorCode"] +"Lock":
                    goodCode = True
                    lockFloor3()
                 # Temp Unlock Third Floor   
                 elif enteredCode == config["ThirdFloorCode"]+"Un-Lock":
                    goodCode = True
                    tempUnlockFloor3()
                 # Client Temp Unlock Third Floor   
                 elif enteredCode == config["ClientCode"]+"Un-Lock":
                    goodCode = True
                    tempUnlockFloor3()
                 # Lock Penthouse
                 elif enteredCode == config["PenthouseCode"]+"Lock":
                    goodCode = True
                    lockPenthouse()
                 # Temp Unlock Penthouse   
                 elif enteredCode == config["PenthouseCode"]+"Un-Lock":
                    goodCode = True
                    tempUnlockPenthouse()
                 # Master Unlock Code
                 # Unlock both Penthouse and Third Floors
                 elif enteredCode == config["MasterCode"]+"Un-Lock":
                    masterUnlock = True
                    goodCode = True
                    relay.ON_3()
                    relay.ON_4()
                    call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Both unlock.m4a"])
                    report("Third & Fourth Floor Un-Locked")
                    clear()
                 # Master Lock Code
                 # Lock both the Penthouse and Third Floors
                 elif enteredCode == config["MasterCode"]+"Lock":
                    masterUnlock = False
                    goodCode = True
                    relay.OFF_3()
                    relay.OFF_4()
                    call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Both lock.m4a"])
                    report("Third & Fourth Floor Locked")
                    clear()
                    
                 else: #wrong code entered
                    report("Wrong Code")
                    call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Try again.m4a"])
                    clear()


           if keyCount>7: #User seems to be mashing keys willy nilly
              report("Just hitting buttions")
              call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/You don't know the code.m4a"])
              clear()

           if (key == "Un-Lock") | (key == "Lock"):
              if (keyCount > 3) & (keyCount < 6):
                 report("Meh")
                 call(["omxplayer", "/home/pi/elevator/ElevatorPython/resource/Meh.m4a"])
                 clear()

def timeLock(): #put lock all on the queue
   for value in config["MasterCode"]:
      threadQueue.put([value, time.time()])
   threadQueue.put(["Lock",time.time()])

def clear():
   global enteredCode
   global keyCount
   global startTime
   global intraKeyTime
   enteredCode = ""
   keyCount = 0
   startTime = 0
   intraKeyTime = 0

def report(message):
##   formattedMessage = "events title="'"%s"'"" % message
##   call(['curl',
##         '-i',
##         '-XPOST',
##         'http://ward.filmworkers.com:8086/write?db=access',
##         '--data-binary',
##         formattedMessage])

##   json_body = [
##      {
##       "measurement": "events",
##       "tags":{},
####     "time":"",
##       "fields": {
##       "title": message
##         }
##      }
##   ]
##   database = InfluxDBClient('ward.filmworkers.com', 8086,'','','access')
##   database.write_points(json_body)
   print(message, time.ctime())

report("Reboot")   

keyPadScanThread = Thread(target = keyPadScan)
supervisorThread = Thread(target = supervisor)
relockThread = Thread(target = relock)
timerThread = Thread(target = timer)

supervisorThread.start()
relockThread.start()
keyPadScanThread.start()
timerThread.start()

# Lock both Floors everyday
schedule.every().day.at(config["AllLockTime"]).do(timeLock)

while True:
   schedule.run_pending()
   time.sleep(10)

