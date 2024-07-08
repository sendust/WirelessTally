from machine import Pin, ADC
import time


class BATTERY:
    
    
    def __init__(self, ch_adc, pin_read):
        self.adc = ADC(ch_adc)
        self.read_enable = Pin(pin_read, Pin.OUT)
        self.read_enable.value(0)
        self.level = 0
        self.level_queue = [0]
        self.average = 0
        self.table_adc = [40000, 41400, 43000,44500, 46000,
                               47500, 49000, 50550, 52100, 53600,
                               55200, 56700, 58000, 59600]
        self.table_voltage = [2.9, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5,
                              3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.2]
        
    def read_adc(self):
        self.read_enable.value(1)
        value = self.adc.read_u16()
        self.read_enable.value(0)
        self.level = value
        self.level_queue.append(value)
        self.average = sum(self.level_queue) / len(self.level_queue)
        while (len(self.level_queue)> 20):
            self.level_queue.pop(0)
        return value

    def get_level(self):
        return self.level
        
    def get_voltage(self):
        voltage = self.table_voltage[0]
        for i in range(14):
            if self.average > self.table_adc[i]:
                voltage = self.table_voltage[i]
        return voltage
    
    
bl = BATTERY(2, 27)     # ADC channel number, read enable pin number



while True:
    print(bl.read_adc(), bl.get_voltage())
    time.sleep_ms(50)