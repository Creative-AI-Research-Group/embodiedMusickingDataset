#
# Blue Haze
# Bitalino class
# 4 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from bitalinoReader import BITalino


class Bitalino:
    def __init__(self):
        # BITalino instantiate object
        bitalino_mac_address = "98:D3:B1:FD:3D:1F"
        self.n_samples = 10
        self.digital_output = [1, 1]

        # Connect to BITalino
        self.bitalino = BITalino(bitalino_mac_address)

        # Set battery threshold
        self.bitalino.battery(30)

        # Read BITalino version
        print(self.bitalino.version())

    def bitalino_read(self):
        # Turn BITalino led on
        self.bitalino.trigger(self.digital_output)

        return self.bitalino.read(self.n_samples)

    def bitalino_terminate(self):
        # Stop Bitalino acquisition
        self.bitalino.stop()

        # Close Bitalino connection
        self.bitalino.close()
