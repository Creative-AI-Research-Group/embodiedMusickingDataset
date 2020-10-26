#
# Blue Haze
# Play Back Track
# 26 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtMultimedia import QSoundEffect
from PySide2.QtCore import QUrl


class PlayBackTrack:
    def __init__(self):
        self.player = QSoundEffect()

    def play(self, file_name):
        self.player.setSource(QUrl.fromLocalFile(file_name))
        self.player.play()

    def stop(self):
        self.player.stop()