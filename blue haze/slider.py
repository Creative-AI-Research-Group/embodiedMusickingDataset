#
# Blue Haze
# 22 Jan 2021
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

# download pip install https://github.com/drewarnett/pypicoboard/archive/master.zip
# how to install the drivers: https://cdn.sparkfun.com/datasheets/Widgets/picoboard03.pdf

from picoboard import PicoBoard
import modules.config as cfg


class Slider:
    def __init__(self):
        self.pb = PicoBoard(cfg.PICOBOARD_PORT)

    def slider_value(self):
        readings = self.pb.read()
        slider = readings['slider']
        slider = int(slider / 100)
        if slider > 100:
            slider = 100
        return slider
