#  Wireless tally system,
#  code managed by sendust, SBS
#  2024/2/29
#  2024/7/3 swap up, down button



from ssd1306 import SSD1306_I2C
from machine import Pin, I2C, Timer
from sx127x import RADIO
import time, json


class button:
    def __init__(self, pinno, name):
        self.btn = Pin(pinno, Pin.IN, Pin.PULL_UP)
        self.prev = 1
        self.name = name
        self.list_result = [0, 0, name, 0] # prev/next = 00 01 10 11
        
    def read(self):
        result = 0
        now = self.btn.value()
        result = self.list_result[self.prev * 2 + now]
        self.prev = now
        return result
        
class GPO:
    def __init__(self, pinno, default=0):
        self.pin = Pin(pinno, Pin.OUT)
        self.pin.value(default)
        self.value = default
        
    def value(self, value):
        self.pin.value(value)
        self.value = value
    
    def toggle(self, t = 0):
        self.value = not self.value
        self.pin.value(self.value)
        print("toggle")



def get_next_indexl(length):
    list_index = []
    for i in range(1, length):
        list_index.append(i)
    list_index.append(length-1)
    return list_index

def get_prev_indexl(length):
    list_index = []
    list_index.append(0)
    for i in range(0, length-1):
        list_index.append(i)
    return list_index


class menu:
    item = ["frequency", "power", "test", "about"]
    value = {}
    value["frequency"] = ["430000", "431000", "432000", "433000", "434000", 
                "435000", "436000", "437000", "438000", "439000", "440000",
                "441000", "442000", "443000", "444000", "445000", "446000"]
    value["power"] = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    value["test"] = ["off", "mode1", "mode2"]
    value["about"] = ["v0.1", "sendust", "SX1278", "RP2040", "LoRa TX"]
    
    item_sel = 0
    #item_sel_next = [1, 2, 3, 0]

    item_sel_next =[]
    for i in range(1, len(item)):
        item_sel_next.append(i)
    item_sel_next.append(0)


    value_sel = {}
    value_sel["frequency"] = 2
    value_sel["power"] = 8
    value_sel["test"] = 0
    value_sel["about"] = 2
    
    list_load_save = ["frequency", "power"]
    
    on_change_fn = {}
    for each in item:
        on_change_fn[each] = print


    value_sel_next = {}
    value_sel_next["frequency"] = get_next_indexl(len(value["frequency"]))
    value_sel_next["power"] = get_next_indexl(len(value["power"]))
    value_sel_next["test"] = get_next_indexl(len(value["test"]))
    value_sel_next["about"] = get_next_indexl(len(value["about"]))
    
    value_sel_prev = {}
    value_sel_prev["frequency"] = get_prev_indexl(len(value["frequency"]))
    value_sel_prev["power"] = get_prev_indexl(len(value["power"])) 
    value_sel_prev["test"] = get_prev_indexl(len(value["test"])) 
    value_sel_prev["about"] = get_prev_indexl(len(value["about"])) 
   

    def menu_save(self):
        cfg_save = {}
        for each in self.list_load_save:
            cfg_save[each] = self.value_sel[each]
        try:
            with open('config.cfg', 'w') as f:
                print(f'cfg save result = {f.write(json.dumps(cfg_save))}')
        except Exception as e:
            print(e)

    def menu_load(self):
        cfg_load = {}
        try:
            with open('config.cfg', 'r') as f:
                cfg_load = json.loads(f.read())
            
            for each in cfg_load:
                self.value_sel[each] = cfg_load[each]
                print(f'cfg loaded..  {each} -> {cfg_load[each]}')
        except Exception as e:
            print(e)


    def set_on_change_fn(self, name_item, fn):
        self.on_change_fn[name_item] = fn

    def get_item(self):
        return self.item[self.item_sel]
    
    def get_item_next(self):
        self.item_sel = self.item_sel_next[self.item_sel]
        return self.get_item()
    
    def get_value(self, name_item):
        return self.value[name_item][self.value_sel[name_item]]
    
    def get_value_next(self, name_item):
        self.value_sel[name_item] = self.value_sel_next[name_item][self.value_sel[name_item]]
        self.on_change_fn[self.item[self.item_sel]]([self.item[self.item_sel], self.get_value(name_item)])
        return self.get_value(name_item)
    
    def get_value_prev(self, name_item):
        self.value_sel[name_item] = self.value_sel_prev[name_item][self.value_sel[name_item]]
        self.on_change_fn[self.item[self.item_sel]]([self.item[self.item_sel], self.get_value(name_item)])
        return self.get_value(name_item)
    
class TIMER_ONCE:
    def __init__(self):
        self.tm_start = time.ticks_ms()
        self.interval = 1000
        self.isfinished = True
    
    def set_interval(self, intval):
        self.isfinished = False
        self.tm_start = time.ticks_ms()
        self.interval = intval
        
    def run(self):
        result = False
        if (not self.isfinished and (time.ticks_ms() - self.tm_start) > self.interval):
            self.isfinished = True
            return True
        else:
            return False
          

class TIMER_REPEAT:
    def __init__(self):
        self.tm_start = time.ticks_ms()
        self.interval = 1000
        self.isfinished = True
    
    def set_interval(self, intval):
        self.isfinished = False
        self.tm_start = time.ticks_ms()
        self.interval = intval
        
    def run(self):
        if (not self.isfinished and (time.ticks_ms() - self.tm_start) > self.interval):
            self.tm_start = time.ticks_ms()
            return True
        else:
            return False

    def reset(self):
        self.isfinished = False
        self.tm_start = time.ticks_ms()

    def halt(self):
        self.isfinished = True


class FCS:
    def __init__(self):
        self.stream = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.next = []
        l = len(self.stream)
        for i in range(len(self.stream)):
            self.next.append(i+1)
        self.next[l-1] = 0
        self.index = l-1
        
    def get_next(self):
        self.index = self.next[self.index]
        return self.stream[self.index]



class TALLYS:

    mode1 = ["1111111111", "0000000000"]
    mode1_next = [1, 0]
    mode1_sel = 0
    
    mode2 = ["0111111111", "1011111111", "1101111111", "1110111111", 
    "1111011111", "1111101111", "1111110111", "1111111011", 
    "1111111101", "1111111110"]
    mode2_next = [1,2,3,4,5,6,7,8,9,0]
    mode2_sel = 0
    
    def __init__(self):
        self.list_pins = [16, 17, 18, 19, 20, 21, 22, 26, 12, 13]
        self.tally_pins = []
        for each in self.list_pins:
            self.tally_pins.append(Pin(each, Pin.IN, Pin.PULL_UP))
        self.count = 0
        

        
    def get_tally(self):
        result = ""
        for each in self.tally_pins:
            result += str(each.value())
        return result
        
    def get_tally_mode1(self):
        result = self.mode1[self.mode1_sel]
        self.mode1_sel = self.mode1_next[self.mode1_sel]
        return result    

    def get_tally_mode2(self):
        result = self.mode2[self.mode2_sel]
        self.mode2_sel = self.mode2_next[self.mode2_sel]
        return result



def on_change_frequency(data):
    global tr, m
    print(f'{data} <-- external function frequency')
    tr.setFrequency(int(data[1]))   # khz -> Mhz

def on_change_power(data):
    global tr
    tr.setPower(int(data[1]), True)
    print(f'{data} <-- external function power')
    
def on_change_test(data):
    global get_tally_fn, tly
    print(f'{data} <-- external function test')
    if data[1] == "mode1":
        get_tally_fn = tly.get_tally_mode1
    elif data[1] == "mode2":
        get_tally_fn = tly.get_tally_mode2
    else:
        get_tally_fn = tly.get_tally

def on_receive(tr, payload, crcOk):
    tr.blink()
    payload_string = payload.decode()
    #payload_string = str(payload)
    rssi = tr.getPktRSSI()
    snr  = tr.getSNR()
    print("*** Received message:")
    print(payload_string)
    print("^^^ CrcOk={}, size={}, RSSI={}, SNR={}\n".format(\
           crcOk, len(payload), rssi, snr))


def draw_display():
    global oled, m, heartbeat, framecheck
    try:       
        oled.fill(0)    
        oled.text(m.get_item(), 10, 10)
        oled.text("TX", 100, 10)
        oled.text(str(m.get_value(m.get_item())), 10, 30)
        oled.text(msg_tosend, 5, 50)
        oled.text(f'[{heartbeat.get_next()}]', 100, 30)
        oled.show()
    except Exception as e:
        print(e)

def savemenu(obj_timer):
    global m
    print("save menu...")
    m.menu_save()


tr = RADIO(mode=0)  # LORA=0  FSK=1 OOK=2
tr.setFrequency(465000) # set freq in kHz
tr.setPower(10, True)       # power dBm (RFO pin if False or PA_BOOST pin if True)
tr.setHighPower(False)      # add +3 dB (up to +20 dBm power on PA_BOOST pin)
tr.setOCP(120, True)        # set OCP trimming (> 120 mA if High Power is on)
tr.enableCRC(True, True)    # CRC, CrcAutoClearOff (FSK/OOK mode)
tr.setPllBW(2)      

tr.setBW(500.)    # BW: 7.8...500 kHz
tr.setCR(8)       # CR: 5..8
tr.setSF(10)      # SF: 6...12
tr.setLDRO(False) # Low Datarate Optimize
tr.setPreamble(6) # 6..65535 (8 by default)
tr.setSW(0x12)    # SW allways 0x12   sync word

tr.dump()
tr.collect()

i2c_dev = I2C(1,scl=Pin(11),sda=Pin(10),freq=200000)
i2c_addr = [hex(ii) for ii in i2c_dev.scan()] # get I2C address in hex format
if i2c_addr==[]:
    print('No I2C Display Found') 
    sys.exit() # exit routine if no dev found
else:
    print("I2C Address      : {}".format(i2c_addr[0])) # I2C device address
    print("I2C Configuration: {}".format(i2c_dev)) # print I2C params


oled = SSD1306_I2C(128, 64, i2c_dev) # oled controller (H x V, i2c object)

btn = [button(14, "up"), button(15, "down"), button(3, "enter")]
led_debug = GPO(27, 0)

hb=GPO(25, 0)

m = menu()

m.menu_load()

    
m.set_on_change_fn("frequency", on_change_frequency)
m.set_on_change_fn("power", on_change_power)
m.set_on_change_fn("test", on_change_test)

tr.setFrequency(int(m.get_value("frequency")))
tr.setPower(int(m.get_value("power")), True)


oled.fill(0)
oled.rect(0,0,127,63,1)
oled.rect(0,30,127,10,1)
oled.text("sendust", 10, 13)
oled.text("LORA TX", 10, 43)
oled.show()
time.sleep_ms(500)


oled.fill(0)
oled.text(m.get_item(), 10, 10)
oled.text(m.get_value(m.get_item()), 10, 30)
oled.show()

count = 0

tmr_oled = TIMER_REPEAT()
tmr_oled.set_interval(200)

heartbeat = FCS()
fcs = FCS()
tly = TALLYS()
get_tally_fn = tly.get_tally

msg_tosend = ''
tim = Timer()

try:
    while True:
        msg_tosend = f'{fcs.get_next()}/{get_tally_fn()}'
        tr.send_lora(msg_tosend, False)
        print(f'm.sent..{msg_tosend}')
        hb.toggle()
        draw_display()
            
        for each in btn:
            result_b = each.read()
            if result_b:
                print(result_b)
                tim.init(mode=Timer.ONE_SHOT, period=1000, callback=savemenu)
                if (result_b == "enter"):
                    m.get_item_next()

                if (result_b == "up"):
                    m.get_value_next(m.get_item())
                    
                if (result_b == "down"):
                    m.get_value_prev(m.get_item())
                draw_display()


except KeyboardInterrupt:
    print("Reset Radio...")
    tr.reset()
    