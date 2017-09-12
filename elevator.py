import os
import random
import configparser
#from influxdb import InfluxDBClient
import time
from evdev import InputDevice
from threading import Thread
from queue import Queue
from subprocess import call
import schedule
import automationhat

threadQueue = Queue()
relockQueue = Queue()

voices = ["Alex", "Allison", "Ava", "Daniel", "Fiona", "Karen", "Kate",
          "Lee", "Moira", "Oliver", "Samantha", "Serena", "Susan", "Tessa",
          "Tom", "Veena", "Vicki", "HaleyA", "HaleyB", "HaleyC"]
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "ElevatorConfig.txt")
configFile = configparser.ConfigParser()
configFile.read(CONFIG_FILE)
config = configFile['Configuration']
            
#Global variables
enteredCode = ""
timeStamp = 0
keyCount = 0
masterUnlock = False
goodCode = True
keyPadDisabled = False


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
         floorToLock = relockQueue.get()
         floor = floorToLock[0]
         whenTo = floorToLock[1]
         delay = abs((whenTo +8) - time.time()) #don't hand sleep a negative number
         if (delay > 8):
            delay = 8
         time.sleep(delay)
         if floor == 3:
            lockFloor3()
         if floor == 4:
            lockPenthouse()
            
def keypadDisable():   
    global keyPadDisabled
    keyPadDisabled = True
    
def keypadEnable():
    global keyPadDisabled
    keyPadDisabled = False
    
   
def lockFloor3():
    automationhat.relay.two.off()
    call(["omxplayer", RESOURCE_PATH + "/Third lock.mp3"])
    report("Third Floor Locked")

def lockPenthouse():
    automationhat.relay.three.off()
    call(["omxplayer", RESOURCE_PATH + "/Penthouse lock.mp3"])
    report("Fourth Floor Locked")
    
def tempUnlockFloor3():
    automationhat.relay.two.on()
    if masterUnlock:
       call(["omxplayer", RESOURCE_PATH + "/Third unlock.mp3"])
       report("Third Floor Un-Lock")
    else:
       report("Third floor Temp Un-locked")
       call(["omxplayer", RESOURCE_PATH + "/Third floor temp unlock.mp3"])
       relockQueue.put([3, time.time()])

def tempUnlockPenthouse():
    automationhat.relay.three.on()
    if masterUnlock:
       call(["omxplayer", RESOURCE_PATH + "/Penthouse unlock.mp3"])
       report("Fourth Floor Un-Lock")
    else:
       report("Fourth Floor Temp Un-Locked")
       call(["omxplayer", RESOURCE_PATH + "/Penthouse temp unlock.mp3"])
       relockQueue.put([4, time.time()])

def timer():
    global timeStamp
    global goodCode
    global keyPadDisabled
    global enteredCode
    while True:
        time.sleep(1)
        if int(time.time() - timeStamp > 3):
            if not goodCode:
               report("Bad code entered was " + enteredCode)
               while (threadQueue.qsize() > 0): #Flush queue
                      junk = threadQueue.get()
               clear()
               goodCode = True
               if keyPadDisabled:
                  call(["omxplayer", RESOURCE_PATH + "/KeyPadDisabled.mp3"])
               else:
                  call(["omxplayer", RESOURCE_PATH + "/Try again.mp3"])
   
def supervisor():
    global enteredCode
    global keyCount
    global masterUnlock
    global timeStamp
    global goodCode
    global keyPadDisabled

    while True:
       if threadQueue.not_empty:
           keypress = threadQueue.get()
           goodCode = False
           key = keypress[0]  #Key the user hit
           timeStamp = keypress[1] #When the user hit the key
           keyCount += 1      #How many keys the user has hit
           enteredCode += key      #append key
                       
           if (keyCount == 4) and (not keyPadDisabled):
               if enteredCode == config["ShortFloor3Code"]:
                  goodCode = True
                  clear()
                  tempUnlockFloor3()
               elif enteredCode == config["ShortFloor4Code"]:
                  goodCode = True
                  clear()
                  tempUnlockPenthouse()
               elif enteredCode == config["FreelanceFloor3Code"]:
                  goodCode = True
                  clear()
                  tempUnlockFloor3()
               elif enteredCode == config["FreelanceFloor4Code"]:
                  goodCode = True
                  clear()
                  tempUnlockPenthouse()
               
           if keyCount == 7: #User has entered the right number of keys
              if (key == "Un-Lock") | (key == "Lock"): #If last key hit was lock/unlock
                 # Lock Third Floor
                 if enteredCode == config["ThirdFloorCode"] +"Lock":
                    goodCode = True
                    clear()
                    lockFloor3()
                 # Temp Unlock Third Floor   
                 elif enteredCode == config["ThirdFloorCode"]+"Un-Lock":
                    goodCode = True
                    clear()
                    tempUnlockFloor3()
                 # Client Temp Unlock Third Floor   
                 elif enteredCode == config["ClientCode"]+"Un-Lock":
                    goodCode = True
                    clear()
                    tempUnlockFloor3()
                 # Lock Penthouse
                 elif enteredCode == config["PenthouseCode"]+"Lock":
                    goodCode = True
                    clear()
                    lockPenthouse()
                 # Temp Unlock Penthouse   
                 elif enteredCode == config["PenthouseCode"]+"Un-Lock":
                    goodCode = True
                    clear()
                    tempUnlockPenthouse()
                 # Master Unlock Code
                 # Unlock both Penthouse and Third Floors
                 elif enteredCode == config["MasterCode"]+"Un-Lock":
                    masterUnlock = True
                    goodCode = True
                    clear()
                    automationhat.relay.two.on()
                    automationhat.relay.three.on()
                    call(["omxplayer", RESOURCE_PATH + "/Both unlock.mp3"])
                    report("Third & Fourth Floor Un-Locked")
                 # Master Lock Code
                 # Lock both the Penthouse and Third Floors
                 elif enteredCode == config["MasterCode"]+"Lock":
                    masterUnlock = False
                    goodCode = True
                    clear()
                    automationhat.relay.two.off()
                    automationhat.relay.three.off()
                    call(["omxplayer", RESOURCE_PATH + "/Both lock.mp3"])
                    report("Third & Fourth Floor Locked")
                    
                 else: #wrong code entered
                    report("Wrong Code")
                    call(["omxplayer", RESOURCE_PATH + "/Woopsy.mp3"])
                    clear()


           if keyCount>7: #User seems to be mashing keys willy nilly
              report("Just hitting buttions")
              call(["omxplayer", RESOURCE_PATH + "/You don't know the code.mp3"])
              clear()

           if (key == "Un-Lock") | (key == "Lock"):
              if (keyCount > 3) & (keyCount < 6):
                 report("Meh")
                 call(["omxplayer", RESOURCE_PATH + "/Meh.mp3"])
                 clear()

def timeLock(): #put lock all on the queue
   for value in config["MasterCode"]:
      threadQueue.put([value, time.time()])
   threadQueue.put(["Lock",time.time()])

def clear():
   global enteredCode
   global keyCount
   enteredCode = ""
   keyCount = 0

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
   with open("/home/pi/Desktop/Elevator.log","at", 1) as logFile:
      logFile.write(message + "\t" + time.ctime() +"\n")

report("***Reboot")
automationhat.light.power.on()

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
# Disable Keypad every night
schedule.every().day.at(config["KeyPadLockTime"]).do(keypadDisable)
# Enable Keypad weekday mornings
schedule.every().monday.at(config["KeyPadUnLockTime"]).do(keypadEnable)
schedule.every().tuesday.at(config["KeyPadUnLockTime"]).do(keypadEnable)
schedule.every().wednesday.at(config["KeyPadUnLockTime"]).do(keypadEnable)
schedule.every().thursday.at(config["KeyPadUnLockTime"]).do(keypadEnable)
schedule.every().friday.at(config["KeyPadUnLockTime"]).do(keypadEnable)

while True:
   schedule.run_pending()
   voice = random.choice(voices)
   RESOURCE_PATH = os.path.join(os.path.dirname(__file__), "resource", voice)
   time.sleep(10)

