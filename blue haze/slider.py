"""download pip install https://github.com/drewarnett/pypicoboard/archive/master.zip
COM5 is the picoboard - either USB port works"""

from picoboard import PicoBoard
from time import sleep

pb = PicoBoard('COM5')

while True:
    readings = pb.read()
    slider = readings["slider"]
    button = readings["button"]
    if button > 0:
        button_cond = 'off'
    else:
        button_cond = 'on'
    slider = int(slider / 10)
    if slider > 100:
        slider = 100
    print(f'slider value = {slider}, button condition = {button_cond}')
    sleep(0.1)
