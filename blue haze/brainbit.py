#
# Blue Haze
# Brainbit class
# 4 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from brainbitReader import BrainbitReader

class Brainbit():
    def __init__(self):
        self.brainbit = BrainbitReader()

    def brainbit_read(self):
        return self.brainbit.read()

    def brainbit_terminate(self):
        self.brainbit.terminate()
