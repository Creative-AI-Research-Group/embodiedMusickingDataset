#
# Blue Haze
# Utils module
# 16 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtCore import QObject, Signal, Slot

import logging
import copy

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


class Realsense(Borg, QObject):
    def __init__(self, parent=None, first_time=False):
        super().__init__()
        Borg.__init__(self)

        if parent is not None:
            self.realsense = None
            self.result = Result(parent)

    def start_realsense(self):
        try:
            self.realsense = hw.SkeletonReader()
            self.realsense.start()
        except:
            return_dict = {
                "from": "RealSense",
                "result": False
            }
        else:
            return_dict = {
                "from": "RealSense",
                "result": True
            }
        self.result.emit_signal(return_dict)

    def read_realsense(self):
        return self.realsense.read()


class Brainbit(Borg, QObject):
    def __init__(self, parent=None, first_time=False):
        super().__init__()
        Borg.__init__(self)

        if parent is not None:
            self.brainbit = None
            self.result = Result(parent)

    def start_brainbit(self):
        try:
            self.brainbit = hw.BrainbitReader()
            self.brainbit.start()
        except Exception as err:
            return_dict = {
                "from": "BrainBit",
                "result": False
            }
            logger.error(err)
        else:
            return_dict = {
                "from": "BrainBit",
                "result": True
            }
        self.result.emit_signal(return_dict)

    def read_brainbit(self):
        return self.brainbit.read()


class Result(QObject):
    signal = Signal(dict)

    def __init__(self, parent):
        super().__init__(parent)
        self.signal.connect(super().parent().hw_init_status)

    def emit_signal(self, message_dict):
        self.signal.emit(message_dict)

