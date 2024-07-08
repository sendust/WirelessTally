set device=COM6
python pyboard.py -d %device%  -f cp main_tx.py :main.py
python pyboard.py -d %device% -f cp ssd1306.py :ssd1306.py
python pyboard.py -d %device% -f cp sx127x.py :sx127x.py
pause
