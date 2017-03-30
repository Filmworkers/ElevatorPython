from influxdb import InfluxDBClient
import time
from evdev import InputDevice
from threading import Thread
from queue import Queue
from subprocess import call
import schedule
from relays import Relay

relay = Relay()
threadQueue = Queue()      

#Global variables
enteredCode = ""
intraKeyTime = 0
startTime = 0
keyCount = 0
masterUnlock = False


def keyPadScan():
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
             threadQueue.put([keys[event.code], event.sec])
               
def supervisor():
    global enteredCode
    global intraKeyTime
    global startTime
    global keyCount
    global masterUnlock

    while True:
       if threadQueue.not_empty:
           keypress = threadQueue.get()
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
           if keyCount == 6: #User has entered the right number of keys
              if (key == "Un-Lock") | (key == "Lock"): #If last key hit was lock/unlock
                 if enteredCode == "031775Lock":
                    print("Third Floor Locked", time.ctime())
                    relay.OFF_3()
                    call(["omxplayer", "/home/pi/elevator/resource/Third lock.m4a"])
                    call(['curl',
                          '-i',
                          '-XPOST',
                          'http://ward.filmworkers.com:8086/write?db=access',
                          '--data-binary',
                          'events title="Third Floor Locked"'])
                    clear()
                 elif enteredCode == "031775Un-Lock":
                    print("Third Floor Un-Locked", time.ctime())
                    relay.ON_3()
                    if masterUnlock:
                       call(["omxplayer", "/home/pi/elevator/resource/Third unlock.m4a"])
                       call(['curl',
                             '-i',
                             '-XPOST',
                             'http://ward.filmworkers.com:8086/write?db=access',
                             '--data-binary',
                             'events title="Third Floor Un-Lock"'])

                    else:
                       call(["omxplayer", "/home/pi/elevator/resource/Third floor temp unlock.m4a"])
                       time.sleep(8)
                       relay.OFF_3()
                       call(["omxplayer", "/home/pi/elevator/resource/Third lock.m4a"])
                       call(['curl',
                             '-i',
                             '-XPOST',
                             'http://ward.filmworkers.com:8086/write?db=access',
                             '--data-binary',
                             'events title="Third Floor Temp Un-Lock"'])
                    clear()
                 elif enteredCode == "041775Lock":
                    relay.OFF_4()
                    print("Fourth Floor Locked", time.ctime())
                    call(["omxplayer", "/home/pi/elevator/resource/Penthouse lock.m4a"])
                    call(['curl',
                          '-i',
                          '-XPOST',
                          'http://ward.filmworkers.com:8086/write?db=access',
                          '--data-binary',
                          'events title="Fourth Floor Locked"'])
                    clear()
                 elif enteredCode == "041775Un-Lock":
                    print("Fourth Floor Un-Locked", time.ctime())
                    relay.ON_4()
                    if masterUnlock:
                       call(["omxplayer", "/home/pi/elevator/resource/Penthouse unlock.m4a"])
                       call(['curl',
                             '-i',
                             '-XPOST',
                             'http://ward.filmworkers.com:8086/write?db=access',
                             '--data-binary',
                             'events title="Fourth Floor Un-Lock"'])

                    else:
                       call(["omxplayer", "/home/pi/elevator/resource/Penthouse temp unlock.m4a"])
                       time.sleep(8)
                       relay.OFF_4()
                       call(["omxplayer", "/home/pi/elevator/resource/Penthouse lock.m4a"])
                       call(['curl',
                             '-i',
                             '-XPOST',
                             'http://ward.filmworkers.com:8086/write?db=access',
                             '--data-binary',
                             'events title="Fourth Floor Temp Un-Lock"'])
                    clear()
                 elif enteredCode=="991775Un-Lock":
                    masterUnlock = True
                    print("3&4 Un-Locked", time.ctime())
                    relay.ON_3()
                    relay.ON_4()
                    call(["omxplayer", "/home/pi/elevator/resource/Both unlock.m4a"])
                    print(call(['curl',
                          '-i',
                          '-XPOST',
                          'http://ward.filmworkers.com:8086/write?db=access',
                          '--data-binary',
                          'events title="Third & Fourth Floor Un-Locked"']))
                    clear()
                 elif enteredCode == "991775Lock":
                    masterUnlock = False
                    print("3&4 Locked", time.ctime())
                    relay.OFF_3()
                    relay.OFF_4()
                    call(["omxplayer", "/home/pi/elevator/resource/Both lock.m4a"])
                    call(['curl',
                          '-i',
                          '-XPOST',
                          'http://ward.filmworkers.com:8086/write?db=access',
                          '--data-binary',
                          'events title="Third & Fourth Floor Locked"'])
                    clear()
                 else: #wrong code entered
                    call(["omxplayer", "/home/pi/elevator/resource/Try again.m4a"])
                    clear()
                  
                  
           if keyCount>7: #User seems to be mashing keys willy nilly
              print("what")
              call(["omxplayer", "/home/pi/elevator/resource/You don't know the code.m4a"])
              clear()

           if (key == "Un-Lock") | (key == "Lock"):
              if (keyCount > 3) & (keyCount < 6):
                 report("Meh")
                 call(["omxplayer", "/home/pi/elevator/resource/Meh.m4a"])
                 clear()
              
def timeLock(): #put lock all on the queue
   threadQueue.put(["9",time.time()])
   threadQueue.put(["9",time.time()])
   threadQueue.put(["1",time.time()])
   threadQueue.put(["7",time.time()])
   threadQueue.put(["7",time.time()])
   threadQueue.put(["5",time.time()])
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
  print(message)
  json_body = [
    {
      "measurement": "events",
      "tags":{},
      "fields": {
      "title": message
         }
      }
   ]

  client = InfluxDBClient('ward.filmworkers.com', 8086,'','','access')
  client.write_points(json_body)

##   messageList = ['curl','-i','-XPOST', 'http://ward.filmworkers.com:8086/write?db=access','--data-binary',
##                  'events title=message']
##   print(messageList)
##   call(messageList)

keyPadScanThread = Thread(target = keyPadScan)
supervisorThread = Thread(target = supervisor)

supervisorThread.start()
keyPadScanThread.start()

schedule.every().day.at("18:00").do(timeLock)

while True:
   schedule.run_pending()
   time.sleep(10)

