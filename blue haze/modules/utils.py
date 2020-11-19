#
# Blue Haze
# Utils module
# 16 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

import logging

import modules.config as cfg
import modules.hardware as hw

logger = logging.getLogger('blue_haze')

if cfg.DEBUG:
    logging.basicConfig(level=logging.DEBUG)

logging.basicConfig(format='(%asctime)s - %(message)s')


'''
BORG class following:
https://code.activestate.com/recipes/66531-singleton-we-dont-need-no-stinkin-singleton-the-bo/
https://www.oreilly.com/library/view/python-cookbook/0596001673/ch05s23.html
'''


class Borg:
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state


class Realsense(Borg):
    def __init__(self, first_time=True):
        Borg.__init__(self)
        if first_time:
            self.realsense = None

    def start_realsense(self):
        self.realsense = hw.SkeletonReader()
        self.realsense.start()

    def read_realsense(self):
        return self.realsense.read()
