from evdev import InputDevice
from threading import Thread
from queue import Queue

code = ""
preTime = 0
startTime = 0
keyCount = 0

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


DEVICE = "/dev/input/by-id/usb-Storm-Interface.com_Storm-Interface-event-kbd"

dev = InputDevice(DEVICE)
dev.grab()  #exclusive access

def keyPadScan(out_q):
   for event in dev.read_loop():
       if event.type==1 and event.value==1:
         if event.code in keys:
            # print("KEY CODE: ", keys[event.code], event.sec)
            out_q.put([keys[event.code], event.sec])
               
def supervisor(in_q):
    global code
    global preTime
    global startTime
    global keyCount

    while True:
       if q.not_empty:
           keypress = in_q.get()
           key=keypress[0]
           time=keypress[1]
           keyCount +=1
           if time - startTime > 5:
              preTime=time
              startTime=time
              clear()
              print()
           if time - preTime < 3:
               code+=key
               preTime=time
           if keyCount==6:
              if code=="031775Lock":
                 print("Third Floor Locked")
                 clear()
                 startTime=0
              if code=="031775Un-Lock":
                 print("Third Floor Un-Locked")
                 clear()
                 startTime=0
              if code=="041775Lock":
                 print("Fourth Floor Locked")
                 clear()
                 startTime=0
              if code=="041775Un-Lock":
                 print("Fourth Floor Un-Locked")
                 clear()
                 startTime=0
                 
           if keyCount>6:
              clear()
              startTime=0
              print("what")
                 
           print(code, preTime, startTime, keyCount)
            
      
def clear():
   global code
   global keyCount
   code=""
   keyCount=0

q = Queue()      
keyPadScanThread = Thread(target=keyPadScan, args=(q,))
supervisorThread = Thread(target=supervisor, args=(q,))

supervisorThread.start()
keyPadScanThread.start()
