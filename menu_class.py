import sys

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
    value["frequency"] = ["500", "510", "520", "530", "540", "550", "560", "570"]
    value["id"] = [1, 2, 3, 4, 5, 6, 7, 8]
    value["dim"] = [20, 30, 40, 50, 60, 70, 80, 90, 100]
    value["about"] = ["v0.1", "sendust", "SX1278", "RP2040", "LoRa"]
    
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
    

    
m = menu()


def on_change_frequency(data):
    print(f'{data} <-- external function')

def on_change_id(data):
    print(f'{data} <-- external function')
    
def on_change_dim(data):
    print(f'{data} <-- external function')
    
m.set_on_change_fn("frequency", on_change_frequency)
m.set_on_change_fn("id", on_change_id)
m.set_on_change_fn("dim", on_change_dim)



while True:
    print(m.get_item())
    print(m.get_value(m.get_item()))
    btn = input("Input u, d, e  ")
    if btn == "e":
        m.get_item_next()
    elif btn == "u":
        m.get_value_next(m.get_item())
    elif btn == "d":
        m.get_value_prev(m.get_item())
