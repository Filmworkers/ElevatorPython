import smbus


bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)


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

