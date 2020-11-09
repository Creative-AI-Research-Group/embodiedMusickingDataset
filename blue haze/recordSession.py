#
# Blue Haze
# Record Session
# 26 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

# todo: 'unduplicate' audio inputs
# todo: improve video quality (change codec)
# todo: create a config file (ex. self.ASSETS_BACKING_AUDIO_FOLDER = 'assets/audio_backing/')

NO_HARDWARE = False

from PySide2.QtMultimedia import QAudioRecorder, QAudioEncoderSettings, QMultimedia
from PySide2.QtCore import QUrl

from checkPlatform import *
from database import *
from playBackTrack import PlayBackTrack
from subprocess import Popen

import shortuuid
import time
import threading
import asyncio

if not NO_HARDWARE:
    from bitalinoReader import *
    from brainbitReader import *
    from skeletontracker import *


def current_milli_time():
    return int(round(time.time() * 1000))


class RecordSession:
    def __init__(self):
        self.session_id = None
        self.session_date = None
        self.session_time_start = None
        self.session_name = None
        self.video_audio_path = None
        self.audio_file_name = None
        self.video_file_name = None
        self.video_process = None
        self.audio_interface = None
        self.plat = check_platform()

        self.audio_recorder = QAudioRecorder()

        self.ASSETS_BACKING_AUDIO_FOLDER = 'assets/audio_backing/'
        self.backing_track_player = PlayBackTrack()

        self.database = None

        self.BITALINO_BAUDRATE = 10
        self.BITALINO_ACQ_CHANNELS = [0]
        self.bitalino = None

        if not NO_HARDWARE:
            self.setup_bitalino()
            self.brainbit = BrainbitReader()
            self.realsense = SkeletonReader()

        self.thread_get_data = None
        self.GET_DATA_INTERVAL = self.BITALINO_BAUDRATE / 1000

        self.loop = None

    def setup_bitalino(self):
        # BITalino instantiate object
        bitalino_mac_address = "98:D3:B1:FD:3D:1F"
        self.n_samples = 1
        self.digital_output = [1, 1]

        # Connect to BITalino
        self.bitalino = BITalino(bitalino_mac_address)

        # Set battery threshold
        self.bitalino.battery(30)

        # Read BITalino version
        print(self.bitalino.version())

    def start_recording(self,
                        session_name,
                        video_audio_path,
                        audio_interface,
                        back_track):
        self.loop = asyncio.get_event_loop()

        self.session_id = shortuuid.uuid()
        self.session_date = time.strftime('%Y%m%d')
        self.session_time_start = current_milli_time()
        self.session_name = '{}_{}_{}'.format(self.session_date,
                                              session_name,
                                              self.session_id)
        self.video_audio_path = video_audio_path
        self.audio_interface = audio_interface

        if not NO_HARDWARE:
            self.bitalino.start(self.BITALINO_BAUDRATE, self.BITALINO_ACQ_CHANNELS)
            self.brainbit.start()
            self.realsense.start()

        self.video_recording()
        self.audio_recording()

        # play the backtrack
        backing_track_file = '{}{}'.format(self.ASSETS_BACKING_AUDIO_FOLDER, back_track)
        self.backing_track_player.play(backing_track_file)

        self.database = Database(self.session_id,
                                 self.session_name,
                                 self.audio_file_name,
                                 self.video_file_name)

        self.thread_get_data = threading.Event()
        self.get_data(self.thread_get_data)

    def video_recording(self):
        # this is an ugly workaround
        # because QMediarecorder
        # doesn't work on Windows
        self.video_file_name = '{}/{}.avi'.format(self.video_audio_path,
                                                  self.session_name)
        # see:
        # https://trac.ffmpeg.org/wiki/Capture/Webcam

        cmd = None

        # everything is hard-coded here
        # what is not good…
        if self.plat == 'Windows':
            cmd = ['ffmpeg', '-f', 'dshow',
                   '-framerate', '30',
                   '-video_size', '1184x656',
                   '-i', 'video=HUE HD Pro Camera',
                   self.video_file_name]
        elif self.plat == 'Darwin':
            # for Mac, we can change it to:
            # ffmpeg -f avfoundation -framerate 30 -video_size 1280x720 -i "Microsoft":none out.avi
            cmd = ['ffmpeg', '-f', 'avfoundation',
                   '-framerate', '30',
                   '-video_size', '1280x720',
                   '-i', '0:none',
                   self.video_file_name]
        elif self.plat == 'Linux':
            cmd = ['ffmpeg', '-f', 'v4l2',
                   '-framerate', '25',
                   '-video_size', '1280x720',
                   '-i', '/dev/video0',
                   self.video_file_name]
        self.video_process = Popen(cmd)

    def audio_recording(self):
        audio_settings = QAudioEncoderSettings()
        self.audio_file_name = '{}/{}.wav'.format(self.video_audio_path,
                                                  self.session_name)
        if self.plat == 'Darwin':
            # MacOs automatically adds .wav by itself
            audio_settings.setCodec('audio/FLAC')
            self.audio_file_name = '{}/{}'.format(self.video_audio_path,
                                                  self.session_name)
        elif self.plat == 'Linux':
            audio_settings.setCodec('audio/x-flac')
        elif self.plat == 'Windows':
            audio_settings.setCodec('audio/pcm')
        audio_settings.setQuality(QMultimedia.VeryHighQuality)
        self.audio_recorder.setEncodingSettings(audio_settings)
        self.audio_recorder.setOutputLocation(QUrl.fromLocalFile(self.audio_file_name))
        self.audio_recorder.setAudioInput(self.audio_interface.deviceName())
        self.audio_recorder.record()

    def get_data(self, stop_thread_get_data):
        timestamp = current_milli_time() - self.session_time_start
        bitalino_data = ['bitalino data here']
        brainbit_data = ['brainbit data here']
        skeleton_data = ['skeleton data here']
        print('TIMESTAMP: {}'.format(timestamp))
        if not NO_HARDWARE:
            bitalino_data = self.bitalino.read(self.n_samples)
            brainbit_data = self.brainbit.read()
            skeleton_data = self.realsense.read()
            print('BITALINO: {}'.format(bitalino_data))
            print('BRAINBIT: {}'.format(brainbit_data))
            print('REALSENSE: {}'.format(skeleton_data))

            # convert ndarrays into lists for MongDB format
            bitalino_data = bitalino_data.tolist()
            brainbit_data = brainbit_data.tolist()

        # insert data in the database
        self.loop.run_until_complete(self.database.insert_document(timestamp,
                                                                   bitalino_data,
                                                                   brainbit_data,
                                                                   skeleton_data))

        if not stop_thread_get_data.is_set():
            # call it again
            threading.Timer(self.GET_DATA_INTERVAL, self.get_data, [self.thread_get_data]).start()

    def stop(self):
        self.backing_track_player.stop()
        self.thread_get_data.set()
        self.audio_recorder.stop()
        self.video_process.terminate()
        self.database.close()
        if not NO_HARDWARE:
            self.bitalino.stop()
            self.brainbit.terminate()
            self.realsense.terminate()

