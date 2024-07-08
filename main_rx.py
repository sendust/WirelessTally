#  Wireless tally system,  (This is  RX module)
#  code managed by sendust, SBS
#   2024/2/29
#   2024/3/12   improve start up screen
#   2024/3/13   PI zero onboard neopixel enabled.
#   2024/3/18   update dim value at bootup
#   2024/4/18   button lock, unlock, LEOLED n : 8 -> 16
#   2024/6/21   swap up, down button pin

 
from ssd1306 import SSD1306_I2C
from machine import Pin, I2C, ADC, Timer
from sx127x import RADIO
import time, neopixel, json, sys


class button:
    def __init__(self, pinno, name):
        self.btn = Pin(pinno, Pin.IN, Pin.PULL_UP)
        self.prev = 1
        self.name = name
        self.long_press = ''
        self.long_count = 0
        self.list_result = [0, 0, name, 0] # prev/next = 00 01 10 11
        
    def read(self):
        result = 0
        now = self.btn.value()
        result = self.list_result[self.prev * 2 + now]
        self.prev = now
        if not (now + self.prev):
            self.long_count += 1
            #print(f'long.. {self.long_count}')
            if (self.long_count == 5):
                result = self.long_press
                #print(result)
        else:
            self.long_count = 0
        return result
        
    def set_long_press(self, action):
        self.long_press = action
        
        
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
    item = ["frequency", "id", "dim", "about"]
    value = {}
    value["frequency"] = ["430000", "431000", "432000", "433000", "434000", 
                "435000", "436000", "437000", "438000", "439000", "440000",
                "441000", "442000", "443000", "444000", "445000", "446000"]
    value["id"] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    value["dim"] = [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    value["about"] = ["v0.2", "sendust", "SX1278", "RP2040", "LoRa RX"]
    
    item_sel = 0
    #item_sel_next = [1, 2, 3, 0]

    item_sel_next =[]
    for i in range(1, len(item)):
        item_sel_next.append(i)
    item_sel_next.append(0)


    value_sel = {}
    value_sel["frequency"] = 2
    value_sel["id"] = 0
    value_sel["dim"] = 3
    value_sel["about"] = 2
    
    list_load_save = ["frequency", "id", "dim"]
    
    on_change_fn = {}
    for each in item:
        on_change_fn[each] = print


    value_sel_next = {}
    value_sel_next["frequency"] = get_next_indexl(len(value["frequency"]))
    value_sel_next["id"] = get_next_indexl(len(value["id"]))
    value_sel_next["dim"] = get_next_indexl(len(value["dim"]))
    value_sel_next["about"] = get_next_indexl(len(value["about"]))
    
    value_sel_prev = {}
    value_sel_prev["frequency"] = get_prev_indexl(len(value["frequency"]))
    value_sel_prev["id"] = get_prev_indexl(len(value["id"])) 
    value_sel_prev["dim"] = get_prev_indexl(len(value["dim"])) 
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
          

class TIMER_REPEAT_BACKUP:
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
        if ((time.ticks_ms() - self.tm_start) < self.interval):
            return False
        else:
            self.tm_start = time.ticks_ms()
            return True and (not self.isfinished)

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


class indicator:    
    payload = ''
    rssi = 0
    snr = 0
    payload_string = ''
    payload_string_prev = '---'


class neoled:
    def __init__(self, n):
        self.np = neopixel.NeoPixel(Pin(8), n)
        self.np_onboard = neopixel.NeoPixel(Pin(16), 1)    # RP2040 Zero onboard WS2812
        self.value = 200
        self.status = 0
    
    def set_dim(self, value):
        self.value = value
    
    def set_on(self):
        n = self.np.n
        for i in range(n):
            self.np[i] = (self.value, 0, 0)
        self.np.write()
        
        self.np_onboard[0] = (self.value, 0, 0)
        self.np_onboard.write()
        self.status = 1
        
    def set_off(self):
        n = self.np.n
        for i in range(n):
            self.np[i] = (0, 0, 0)
        self.np.write()
        
        self.np_onboard[0] = (0, 0, 0)
        self.np_onboard.write()
        
        self.status = 0

class button_lock:
    def __init__(self):
        self.lock_disp = ["UNLOCK", "LOCK"]
        self.lock_status = 1
        
    def get_lock(self):
        return self.lock_status
        
    def toggle_lock(self):
        self.lock_status = not self.lock_status
        
    def get_disp(self):
        return self.lock_disp[self.lock_status]
    
    def set_unlock(self):
        self.lock_status = 0
        
    def set_lock(self):
        self.lock_status = 1
    
    def is_unlocked(self):
        return not self.lock_status

def on_change_frequency(data):
    global tr
    print(f'{data} <-- external function')
    tr.standby()
    tr.setFrequency(int(data[1]))
    tr.collect()
    tr.receive()

def on_change_id(data):
    print(f'{data} <-- external function')
    
def on_change_dim(data):
    global neo
    print(f'{data} <-- external function')
    neo.set_dim(int(int(data[1]) / 100.0 * 255))
    neo.set_on()

def on_receive(tr, payload, crcOk):
    global indr
    if crcOk:
        indr.payload_string = payload.decode()
        control_tally(indr.payload_string)
    else:
        indr.payload_string = "0/0000000000000000"
    #payload_string = str(payload)
    rssi = tr.getPktRSSI()
    snr  = tr.getSNR()
    #print("*** Received message:")
    print(payload)
    print("^^^ CrcOk={}, size={}, RSSI={}, SNR={}\n".format(\
           crcOk, len(payload), rssi, snr))
    indr.rssi = rssi
    indr.snr = snr
    try:
        tmr_oled.reset()
        draw_display()
    except Exception as e:
        print(e)

def draw_display():
    global oled, m, heartbeat, payload_string, bl, indr, lock
    
    try:
        oled.fill(0)
        oled.text(lock.get_disp(), 5, 0)
        oled.text(f'{bl.get_voltage()}v', 80, 0)
        oled.text(m.get_item(), 5, 10)
        oled.text("RX", 100, 10)
        oled.text(str(m.get_value(m.get_item())), 5, 20)
        oled.line(0,35, 127,35,1)
        oled.text(f'{indr.rssi} / {indr.snr}', 5, 40)
        oled.text(f'r={indr.payload_string}', 5, 50)
        oled.text(f'[{heartbeat.get_next()}]', 100, 20)
        oled.show()
    except Exception as e:
        print(e)
            
def enablerx(obj_timer):
    global tr, m
    print("continue receive.....")
    m.menu_save()
    tr.receive()


def control_tally(str_control):
    global m, neo
    t_control = int(str_control[int(m.value_sel["id"])+2])    # TX string : F/1111111111  position 2 == ID(1)
    #print(t_control)
    if not t_control:
        neo.set_on()
    else:
        neo.set_off()


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

tr.onReceive(on_receive) # set the receive callback

indr = indicator()
neo = neoled(16)
neo.set_on()

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
btn[2].set_long_press("lock")


led_debug = GPO(27, 0)

m = menu()
lock = button_lock()

    
m.set_on_change_fn("frequency", on_change_frequency)
m.set_on_change_fn("id", on_change_id)
m.set_on_change_fn("dim", on_change_dim)

m.menu_load()

tr.setFrequency(int(m.get_value("frequency")))
tr.receive()


oled.fill(0)
oled.rect(0,0,127,63,1)
oled.rect(0,30,127,10,1)
oled.text("sendust", 10, 13)
oled.text("LORA RX", 10, 43)
oled.show()
time.sleep_ms(500)

neo.set_dim(int(m.get_value("dim")))
neo.set_off()

oled.fill(0)
oled.text(m.get_item(), 10, 10)
oled.text(m.get_value(m.get_item()), 10, 30)
oled.show()

count = 0

tmr_oled = TIMER_REPEAT()
tmr_oled.set_interval(300)

heartbeat = FCS()
bl = BATTERY(2, 27)     # ADC channel number, read enable pin number

tmr_battery = TIMER_REPEAT()
tmr_battery.set_interval(200)
tmr_lock = TIMER_ONCE()
tim = Timer()

try:
    while True:
        count += 1
        if tmr_oled.run():
            if (indr.payload_string == indr.payload_string_prev):
                indr.payload_string = "No signal"
                indr.rssi = -100
                indr.snr = -100
                neo.set_off()
            draw_display()

        for each in btn:
            result_b = each.read()
            if result_b:
                print(result_b)
                tr.standby()    # Temporary disable receiver
                tim.init(mode=Timer.ONE_SHOT, period=1000, callback=enablerx)
                
                if (result_b == "lock"):
                    lock.set_unlock()
                    tmr_lock.set_interval(4000)    

                if (result_b == "enter"):
                    m.get_item_next()
                    tmr_lock.set_interval(4000)
    
                if lock.is_unlocked():

                    if (result_b == "up"):
                        m.get_value_next(m.get_item())
                        tmr_lock.set_interval(4000)    
                        
                    if (result_b == "down"):
                        m.get_value_prev(m.get_item())
                        tmr_lock.set_interval(4000)    


            draw_display()
        
        if tmr_battery.run():
            print(f'ADC => {bl.read_adc()}')

        if tmr_lock.run():
            lock.set_lock()

        indr.payload_string_prev = indr.payload_string
                
except KeyboardInterrupt:
    print("Reset Radio...")
    tr.reset()
