from evdev import InputDevice
from threading import Thread
from queue import Queue

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
    code = ""
    preTime = 0
    startTime = 0
    while q.not_empty:
        keypress = in_q.get()
        key=keypress[0]
        time=keypress[1]
        if time - startTime > 10:
           startTime=time
           preTime=time
           code=""
           print()
        if time - preTime < 3:
            code+=key
            preTime=time

              
        print(code, preTime, startTime)
            
      
      

q = Queue()      
keyPadScanThread = Thread(target=keyPadScan, args=(q,))
supervisorThread = Thread(target=supervisor, args=(q,))

supervisorThread.start()
keyPadScanThread.start()
