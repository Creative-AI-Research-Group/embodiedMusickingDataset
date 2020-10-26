#
# Blue Haze
# Record Session
# 26 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtMultimedia import QMediaRecorder
from PySide2.QtCore import QUrl

import shortuuid
import time


def current_milli_time():
    return int(round(time.time() * 1000))


class RecordSession:
    def __init__(self):
        self.session_id = None
        self.session_date = None
        self.session_time_start = None
        self.session_name = None
        self.video_audio_path = None
        self.camera = None
        self.camera_recorder = None

    def start_recording(self,
                        session_name,
                        video_audio_path,
                        camera):
        self.session_id = shortuuid.uuid()
        self.session_date = time.strftime('%Y%m%d')
        self.session_time_start = current_milli_time()
        self.session_name = '{}_{}_{}'.format(self.session_date,
                                              session_name,
                                              self.session_id)
        self.video_audio_path = video_audio_path
        self.camera = camera
        # self.video_recording()

    def video_recording(self):
        print('recording')
        self.camera_recorder = QMediaRecorder(self.camera)
        video_file_name = '{}/{}.mp4'.format(self.video_audio_path,
                                        self.session_name)
        print(video_file_name)
        self.camera_recorder.setOutputLocation(QUrl.fromLocalFile(video_file_name))
        self.camera_recorder.record()
        print(self.camera_recorder.state())
        print(self.camera_recorder.status())
        print(self.camera_recorder.error())

    def stop(self):
        print('stop recording')
        # self.camera_recorder.stop()

