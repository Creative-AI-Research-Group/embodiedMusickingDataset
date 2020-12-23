#
# Blue Haze
# Play Back Track
# 26 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtCore import QUrl, QObject, Signal

import modules.utils as utls


class PlayBackTrack():
    def __init__(self, parent=None):
        super().__init__()
        self.player = QMediaPlayer()
        self.is_playing = False
        self.player.mediaStatusChanged[QMediaPlayer.MediaStatus].connect(self.media_status_changed)
        if parent is not None:
            self.result = utls.EmitSignal(parent, parent.back_track_end)

    def play(self, file_name):
        self.player.setMedia(QUrl.fromLocalFile(file_name))
        self.player.play()
        self.is_playing = True

    def stop(self):
        self.player.stop()
        self.is_playing = False

    def media_status_changed(self, status):
        # check if it is the end of the audio file
        if status == QMediaPlayer.EndOfMedia:
            return_dict = {
                'end_of_audio_file': True
            }
            self.result.emit_signal(return_dict)
