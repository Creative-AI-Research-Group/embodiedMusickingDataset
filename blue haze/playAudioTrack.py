#
# Blue Haze
# Play Back Track
# 26 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtMultimedia import QMediaPlayer, QMediaContent
from PySide2.QtCore import QUrl

import modules.utils as utls


class PlayAudioTrack(QMediaPlayer):
    def __init__(self, parent=None):
        super(PlayAudioTrack, self).__init__()
        self.mediaStatusChanged[QMediaPlayer.MediaStatus].connect(self.media_status_changed)
        if parent is not None:
            self.result = utls.EmitSignal(parent, parent.back_track_end)

    def setup_media(self, file_name):
        self.setMedia(QMediaContent(QUrl.fromLocalFile(file_name)))

    def media_status_changed(self, status):
        # check if it is the end of the audio file
        if status == QMediaPlayer.EndOfMedia:
            try:
                return_dict = {
                    'end_of_audio_file': True
                }
                self.result.emit_signal(return_dict)
            except AttributeError:
                pass
