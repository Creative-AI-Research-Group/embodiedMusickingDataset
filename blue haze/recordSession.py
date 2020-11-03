#
# Blue Haze
# Record Session
# 26 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#


from checkPlatform import *
from subprocess import Popen

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
        self.video_process = None

    def start_recording(self,
                        session_name,
                        video_audio_path):
        self.session_id = shortuuid.uuid()
        self.session_date = time.strftime('%Y%m%d')
        self.session_time_start = current_milli_time()
        self.session_name = '{}_{}_{}'.format(self.session_date,
                                              session_name,
                                              self.session_id)
        self.video_audio_path = video_audio_path
        self.video_recording()

    def video_recording(self):
        # this is an ugly workaround
        # because QMediarecorder
        # doesn't work on Windows
        video_file_name = '{}/{}.mp4'.format(self.video_audio_path,
                                             self.session_name)
        # see:
        # https://trac.ffmpeg.org/wiki/Capture/Webcam

        cmd = None
        plat = check_platform()

        if plat == 'Windows':
            cmd = ['ffmpeg', '-f', 'dshow',
                   '-i', 'video=HUE HD Camera',
                   video_file_name]
        elif plat == 'Darwin':
            cmd = ['ffmpeg', '-f', 'avfoundation',
                   '-framerate', '30',
                   '-video_size', '1280x720',
                   '-i', '0:none',
                   video_file_name]
        elif plat == 'Linux':
            cmd = ['ffmpeg', '-f', 'v4l2',
                   '-framerate', '25',
                   '-video_size', '1280x720',
                   '-i', '/dev/video2',
                   video_file_name]
        self.video_process = Popen(cmd)

    # I know Python is not Java, but...
    def stop(self):
        self.video_process.terminate()

    def check_status(self):
        return self.video_process.poll()
