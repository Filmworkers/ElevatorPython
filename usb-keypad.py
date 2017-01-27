from evdev import InputDevice
from threading import Thread
from queue import Queue
from subprocess import call
import smbus

bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

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

class Relay():  
    global bus
    def __init__(self):
        self.DEVICE_ADDRESS = 0x20    #7 bit address (will be left shifted to add the read write bit)
        self.DEVICE_REG_MODE1 = 0x06
        self.DEVICE_REG_DATA = 0xff
        bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
             
    def ON_1(self):
            print ('ON_1...')
            self.DEVICE_REG_DATA &= ~(0x1<<0)  
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
    def ON_2(self):
            print ('ON_2...')
            self.DEVICE_REG_DATA &= ~(0x1<<1)
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
    def ON_3(self):
            print ('ON_3...')
            self.DEVICE_REG_DATA &= ~(0x1<<2)
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
    def ON_4(self):
            print ('ON_4...')
            self.DEVICE_REG_DATA &= ~(0x1<<3)
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
    
    def OFF_1(self):
            print ('OFF_1...')
            self.DEVICE_REG_DATA |= (0x1<<0)
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
    
    def OFF_2(self):
            print ('OFF_2...')
            self.DEVICE_REG_DATA |= (0x1<<1)
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def OFF_3(self):
            print ('OFF_3...')
            self.DEVICE_REG_DATA |= (0x1<<2)
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
    
    def OFF_4(self):
            print ('OFF_4...')
            self.DEVICE_REG_DATA |= (0x1<<3)
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
    
    def ALLON(self):
            print ('ALLON...')
            self.DEVICE_REG_DATA &= ~(0xf<<0)
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
    
    def ALLOFF(self):
            print ('ALLOFF...')
            self.DEVICE_REG_DATA |= (0xf<<0)
            bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

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
              clear()
              preTime=time
              startTime=time
           if time - preTime < 3:
               code+=key
               preTime=time
           if keyCount==6:
              if code=="031775Lock":
                 print("Third Floor Locked")
                 relay.OFF_3()
                 call(["omxplayer", "/home/pi/elevator/resource/Third lock.m4a"])
                 clear()
              if code=="031775Un-Lock":
                 print("Third Floor Un-Locked")
                 relay.ON_3()
                 call(["omxplayer", "/home/pi/elevator/resource/Third unlock.m4a"])
                 clear()
              if code=="041775Lock":
                 relay.OFF_4()
                 print("Fourth Floor Locked")
                 call(["omxplayer", "/home/pi/elevator/resource/Penthouse lock.m4a"])
                 clear()
              if code=="041775Un-Lock":
                 print("Fourth Floor Un-Locked")
                 relay.ON_4()
                 call(["omxplayer", "/home/pi/elevator/resource/Penthouse unlock.m4a"])
                 clear()
              if code=="001775Un-Lock":
                 print("3&4 Un-Locked")
                 relay.ON_3()
                 relay.ON_4()
                 call(["omxplayer", "/home/pi/elevator/resource/Both unlock.m4a"])
                 clear()
              if code=="001775Lock":
                 print("3&4 Locked")
                 relay.OFF_3()
                 relay.OFF_4()
                 call(["omxplayer", "/home/pi/elevator/resource/Both lock.m4a"])
                 clear()
               
           if keyCount>6:
              print("what")
              call(["omxplayer", "/home/pi/elevator/resource/You don't know the code.m4a"])
              clear()
           #print(code, preTime, startTime, keyCount)
            
      
def clear():
   global code
   global keyCount
   global startTime
   global preTime
   code=""
   keyCount=0
   startTime=0
   preTime=0

relay = Relay()
q = Queue()      
keyPadScanThread = Thread(target=keyPadScan, args=(q,))
supervisorThread = Thread(target=supervisor, args=(q,))

supervisorThread.start()
keyPadScanThread.start()
