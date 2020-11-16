#
# Blue Haze
# Record Session
# 26 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtMultimedia import QAudioRecorder, QAudioEncoderSettings, QMultimedia
from PySide2.QtCore import QUrl
from database import *
from playBackTrack import PlayBackTrack
from subprocess import Popen

import shortuuid
import time
import threading
import asyncio

import modules.utils as utls
import modules.config as cfg

if cfg.HARDWARE:
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
        self.video_source = None

        self.audio_recorder = QAudioRecorder()

        self.backing_track_player = PlayBackTrack()

        self.database = None

        self.bitalino = None
        self.body_parts_list = ['nose', 'neck', 'r_shoudler', 'r_elbow', 'r_wrist', 'l_shoudler',
                                'l_elbow', 'l_wrist', 'r_eye', 'l_eye', 'r_ear', 'l_ear']
        self.brainbit_eeg_labels = ['eeg-T3', 'eeg-T4', 'eeg-O1', 'eeg-O2']

        if cfg.HARDWARE:
            self.setup_bitalino()
            self.brainbit = BrainbitReader()
            self.realsense = SkeletonReader()

        self.thread_get_data = None
        self.GET_DATA_INTERVAL = cfg.BITALINO_BAUDRATE / 1000

        self.loop = None

    def setup_bitalino(self):
        # BITalino instantiate object
        self.n_samples = 1
        self.digital_output = [1, 1]

        # Connect to BITalino
        self.bitalino = BITalino(cfg.BITALINO_MAC_ADDRESS)

        # Set battery threshold
        self.bitalino.battery(30)

        # Read BITalino version
        logging.info(self.bitalino.version())

    def start_recording(self,
                        session_name,
                        video_audio_path,
                        video_source,
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
        self.video_source = video_source
        self.audio_interface = audio_interface

        if cfg.HARDWARE:
            self.bitalino.start(cfg.BITALINO_BAUDRATE, cfg.BITALINO_ACQ_CHANNELS)
            self.brainbit.start()
            self.realsense.start()

        self.video_recording()
        self.audio_recording()

        # play the backtrack
        backing_track_file = '{}{}'.format(cfg.ASSETS_BACKING_AUDIO_FOLDER, back_track)
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
        # keep an eye regularly on:
        # https://doc.qt.io/qt-5/qtmultimedia-windows.html
        # to see if it gets supported
        # on Windows
        self.video_file_name = '{}/{}.avi'.format(self.video_audio_path,
                                                  self.session_name)

        # see:
        # https://trac.ffmpeg.org/wiki/Capture/Webcam
        cmd = None

        # list video and audio devices on Windows:
        # https://trac.ffmpeg.org/wiki/DirectShow
        # ffmpeg -list_devices true -f dshow -i dummy
        if utls.PLATFORM == 'Windows':
            cmd = ['ffmpeg', '-f', 'dshow',
                   '-framerate', '30',
                   '-i', 'video={}'.format(self.video_source),
                   '-q:v', '3',
                   '-b:v', '2M',
                   self.video_file_name]
        elif utls.PLATFORM == 'Darwin':
            # for Mac, we can change it to:
            # ffmpeg -f avfoundation -framerate 30 -video_size 1280x720 -i "Microsoft":none out.avi
            # https://trac.ffmpeg.org/wiki/Capture/Webcam
            # ffmpeg -f avfoundation -list_devices true -i ""
            cmd = ['ffmpeg', '-f', 'avfoundation',
                   '-framerate', '30',
                   '-video_size', '1280x720',
                   '-i', '0:none',
                   self.video_file_name]
        elif utls.PLATFORM == 'Linux':
            # https://trac.ffmpeg.org/wiki/Capture/Webcam
            # v4l2-ctl --list-devices
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
        if utls.PLATFORM == 'Darwin':
            # MacOs automatically adds .wav by itself
            audio_settings.setCodec('audio/FLAC')
            self.audio_file_name = '{}/{}'.format(self.video_audio_path,
                                                  self.session_name)
        elif utls.PLATFORM == 'Linux':
            audio_settings.setCodec('audio/x-flac')
        elif utls.PLATFORM == 'Windows':
            audio_settings.setCodec('audio/pcm')
        audio_settings.setQuality(QMultimedia.VeryHighQuality)
        self.audio_recorder.setEncodingSettings(audio_settings)
        self.audio_recorder.setVolume(0.3)
        self.audio_recorder.setOutputLocation(QUrl.fromLocalFile(self.audio_file_name))
        self.audio_recorder.setAudioInput(self.audio_interface.deviceName())
        self.audio_recorder.record()

    def get_data(self, stop_thread_get_data):
        timestamp = current_milli_time() - self.session_time_start
        bitalino_data = ['bitalino data here']
        brainbit_data = ['brainbit data here']
        skeleton_data = ['skeleton data here']
        if cfg.HARDWARE:
            bitalino_data = self.bitalino.read(self.n_samples)
            raw_brainbit_data = self.brainbit.read()
            raw_skeleton_data = self.realsense.read()

            # parse raw skeleton data
            skeleton_data = self.skeleton_parse(raw_skeleton_data)

            # slicing usable bitalino data and convert to list
            bitalino_data = bitalino_data[0, -1]
            bitalino_data = bitalino_data.tolist()

            # parse and label brainbit data
            brainbit_data = self.brainbit_parse(raw_brainbit_data)

            logging.debug('BITALINO: {}'.format(bitalino_data))
            logging.debug('BRAINBIT: {}'.format(brainbit_data))
            logging.debug('REALSENSE: {}'.format(skeleton_data))

        # insert data in the database
        self.loop.run_until_complete(self.database.insert_document(timestamp,
                                                                   bitalino_data,
                                                                   brainbit_data,
                                                                   skeleton_data))

        if not stop_thread_get_data.is_set():
            # call it again
            threading.Timer(self.GET_DATA_INTERVAL, self.get_data, [self.thread_get_data]).start()

    def brainbit_parse(self, raw_brainbit_data):
        # setup a temp list for each parse
        temp_list = []

        # parse only the fields we need from timestamp, eegt2, eegt4, eeg01, eeg02, X, X, X, X, X, X, boardID, battery
        for raw in raw_brainbit_data[1:5]:
            temp_eeg_list = []
            for eeg in raw:
                temp_eeg_list.append(eeg)
            temp_list.append(temp_eeg_list)

        # zip and return
        brainbit_data = list(zip(self.brainbit_eeg_labels, temp_list))
        return brainbit_data

    def skeleton_parse(self, raw_skeleton_data):
        # create temp lists
        joint_coord_list = []
        coord_conf_list = []

        # parse iterables to lists
        for keypoint in raw_skeleton_data:
            # extract joint coords for 1st 8 & last 4 joints
            for joint in keypoint[0:1]:
                # 1st 8
                for coords in joint[:8]:
                    joint_coord_list.append(coords[0:2])
                # last 4
                for coords in joint[-4:]:
                    joint_coord_list.append(coords[0:2])

            # extract coord confidences for  1st 8 & last 4 joints
            for conf in keypoint[1:2]:
                # 1st 8
                for value in conf[:8]:
                    coord_conf_list.append(value)
                # last 4
                for value in conf[-4:]:
                    coord_conf_list.append(value)

        # zip all arrays and return
        skeleton_data = list(zip(self.body_parts_list, joint_coord_list, coord_conf_list))
        return skeleton_data

    def stop(self):
        self.backing_track_player.stop()
        self.thread_get_data.set()
        self.audio_recorder.stop()
        self.video_process.terminate()
        self.database.close()
        if cfg.HARDWARE:
            self.bitalino.stop()
            self.brainbit.terminate()
            self.realsense.terminate()

