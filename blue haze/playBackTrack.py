#
# Blue Haze
# Play Back Track
# 26 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtCore import QUrl


class PlayBackTrack:
    def __init__(self):
        self.player = QMediaPlayer()
        self.is_playing = False

    def play(self, file_name):
        self.player.setMedia(QUrl.fromLocalFile(file_name))
        self.player.play()
        self.is_playing = True

    def stop(self):
        self.player.stop()
        self.is_playing = False
