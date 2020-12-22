#
# Blue Haze
# Utils module
# 16 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtCore import QObject, Signal

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


class Hardware(Borg, QObject):
    def __init__(self, parent=None):
        super().__init__()
        Borg.__init__(self)

        if parent is not None:
            self.result = EmitSignal(parent, dict(), parent.hw_init_status)
            self.realsense = None
            self.brainbit = None
            self.bitalino = None

    def start_realsense(self):
        try:
            self.realsense = hw.SkeletonReader()
            self.realsense.start()
        except Exception as err:
            return_dict = {
                "from": "RealSense",
                "result": False
            }
            logger.error(err)
        else:
            return_dict = {
                "from": "RealSense",
                "result": True
            }
        self.result.emit_signal(return_dict)

    def read_realsense(self):
        return self.realsense.read()

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

    def start_bitalino(self):
        try:
            # BITalino instantiate object
            self.n_samples = 1
            self.digital_output = [1, 1]

            # Connect to BITalino
            self.bitalino = hw.BITalino(cfg.BITALINO_MAC_ADDRESS)

            # Set battery threshold
            self.bitalino.battery(30)

            # Read BITalino version
            logger.info(self.bitalino.version())

            # start bitalino
            self.bitalino.start(cfg.BITALINO_BAUDRATE, cfg.BITALINO_ACQ_CHANNELS)
        except Exception as err:
            return_dict = {
                "from": "Bitalino",
                "result": False
            }
            logger.error(err)
        else:
            return_dict = {
                "from": "Bitalino",
                "result": True
            }

        self.result.emit_signal(return_dict)

    def read_bitalino(self):
        return self.bitalino.read(self.n_samples)

    def stop(self):
        """
            bitalino.stop()
            brainbit.terminate()
            realsense.terminate()
        """
        pass


class EmitSignal(QObject):
    signal = Signal(dict)

    def __init__(self, parent, signal_type, fn_name):
        # self.signal = Signal(dict())
        super().__init__(parent)
        self.signal.connect(fn_name)

    def emit_signal(self, message_dict):
        self.signal.emit(message_dict)

