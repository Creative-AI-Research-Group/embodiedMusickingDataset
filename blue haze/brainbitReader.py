"""script for communicating to the BrainBit via the BrainFlow library"""

import numpy as np

import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
import time


class BrainbitReader():
    def __init__(self):

        # Establish all paramters for Brainflow
        self.params = BrainFlowInputParams ()

        # Assign the BrainBit as the board
        self.params.board_id = 7

        # set it logging
        BoardShim.enable_dev_board_logger()
        print('BrainBit reader ready')

    def start(self):
        # instantiate the board reading
        self.board = BoardShim(self.params.board_id, self.params)

        self.board.prepare_session ()

        # board.start_stream () # use this for default options
        self.board.start_stream() # removed 48000
        print ('BrainBit stream started')

    def read(self):
        # data = board.get_current_board_data (256) # get latest 256 packages or less, doesnt remove them from internal buffer
        self.data = self.board.get_board_data () # get all data and remove it from internal buffer
        return self.data

    def terminate(self):
        self.board.stop_stream()
        self.board.release_session()


if __name__ == "__main__":
    board = BrainbitReader()
    brainbit_eeg_labels = ['T3', 'T4', 'O1', 'O2']
    board.start()

    for i in range(100):
        temp_list = []
        data = board.read()

        for raw in data[1:5]:
            temp_eeg_list = []
            for eeg in raw:
                temp_eeg_list.append(eeg)
            temp_list.append(temp_eeg_list)

        brainbit_data = list(zip(brainbit_eeg_labels, temp_list))

        print(brainbit_data)
        time.sleep(0.1)

    board.terminate()
