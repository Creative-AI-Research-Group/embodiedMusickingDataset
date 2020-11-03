#
# Blue Haze
# 19 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtWidgets import *
from PySide2.QtMultimedia import *
from PySide2.QtMultimediaWidgets import QCameraViewfinder
from PySide2.QtCore import Slot, Qt, QThread, QDir, QUrl
from glob import glob
from playBackTrack import PlayBackTrack
from recordSession import RecordSession
from checkPlatform import *

import os
import sys
import asyncio

# from bitalinoReader import BITalino
# from time import sleep, localtime
# from skeletontracker import SkeletonReader
# from brainbitReader import BrainbitReader


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.session_name = QLineEdit()
        self.video_file_path = QLineEdit()
        self.list_cameras = QComboBox()
        self.list_audio_devices = QComboBox()
        self.list_backing_tracks = QComboBox()
        self.record_stop_button = QPushButton('Record session')
        self.play_stop_backing_track_button = QPushButton('Play backing track')
        self.backing_track_player = PlayBackTrack()
        self.recording_label = QLabel()
        self.recording = False

        self.record_session = RecordSession()

        # platform
        self.plat = check_platform()

        # folders
        self.ASSETS_IMAGES_FOLDER = 'assets/images/'
        self.ASSETS_BACKING_AUDIO_FOLDER = 'assets/audio_backing/'

        # # BITalino instantiate object
        # bitalino_macAddress = "98:D3:B1:FD:3D:1F"
        # self.nSamples = 10
        # self.digitalOutput = [1, 1]
        # # Connect to BITalino
        # self.bitalino = BITalino(bitalino_macAddress)
        # # Set battery threshold
        # self.bitalino.battery(30)
        # # Read BITalino version
        # print(self.bitalino.version())
        #
        # # BrainBit instantiate object
        # self.brainbit = BrainbitReader()
        #
        # # RealSense & Skeleton startup
        # self.skeleton = SkeletonReader()

        self.view_finder = QCameraViewfinder()

        self.get_list_cameras()
        self.get_list_audio_devices()
        self.get_list_backing_tracks()

        self.setup_ui()

        self.camera = QCamera(self.list_cameras.currentData())
        self.start_camera()

        # # Start HW device streams
        # acqChannels = [0]  # removed, 1, 2, 3, 4, 5]
        # samplingRate = baudrate
        # self.bitalino.start(samplingRate, acqChannels)
        # self.brainbit.start()
        # self.skeleton.start()

    def setup_ui(self):
        # fields
        fields_group_box = QGroupBox()
        fields = QGridLayout()
        fields.setSpacing(8)

        # session name
        session_name_label = QLabel('Session name: ')

        # video file path
        video_path_file_label = QLabel('Video/Audio path: ')
        folder_browser_button = QPushButton('Browse directories')
        # connect the folder_browser_button signal
        folder_browser_button.clicked.connect(self.show_folder_browser)

        # camera selection
        list_cameras_label = QLabel('Available cameras: ')
        refresh_cameras_button = QPushButton('Refresh cameras')
        # connect the button signal
        refresh_cameras_button.clicked.connect(self.refresh_cameras)
        # connect the list of cameras signal
        self.list_cameras.activated[str].connect(self.change_camera)

        # audio input selection
        list_audio_label = QLabel('Available audio input: ')
        refresh_audio_input_button = QPushButton('Refresh audio input')
        # connect the refresh_audio_input_button signal
        refresh_audio_input_button.clicked.connect(self.refresh_audio_input)

        # backing track selection
        list_backing_tracks_label = QLabel('Available backing tracks: ')
        # connect the play_stop_backing_track_button signal
        self.play_stop_backing_track_button.clicked.connect(self.play_stop_backing_track)

        # fields layout
        # session name
        fields.addWidget(session_name_label, 0, 0)
        fields.addWidget(self.session_name, 0, 1)

        # video path
        fields.addWidget(video_path_file_label, 1, 0)
        fields.addWidget(self.video_file_path, 1, 1)
        fields.addWidget(folder_browser_button, 1, 2)

        # cameras
        fields.addWidget(list_cameras_label, 2, 0)
        fields.addWidget(self.list_cameras, 2, 1)
        fields.addWidget(refresh_cameras_button, 2, 2)

        # audio
        fields.addWidget(list_audio_label, 3, 0)
        fields.addWidget(self.list_audio_devices, 3, 1)
        fields.addWidget(refresh_audio_input_button, 3, 2)

        # backing tracks
        fields.addWidget(list_backing_tracks_label, 4, 0)
        fields.addWidget(self.list_backing_tracks, 4, 1)
        fields.addWidget(self.play_stop_backing_track_button, 4, 2)

        fields_group_box.setLayout(fields)

        # viewfinder
        view_finder_group_box = QGroupBox()
        view_finder_layout = QGridLayout()
        view_finder_layout.addWidget(self.view_finder, 1, 1)
        view_finder_group_box.setLayout(view_finder_layout)

        # record/stop button
        record_button_group_box = QGroupBox()
        record_button_layout = QGridLayout()
        # rec image
        self.recording_label.setPixmap(self.ASSETS_IMAGES_FOLDER + 'gray_rec.png')
        # need to find a better solution
        # this is a workaround
        empty_label = QLabel(' ')
        record_button_layout.addWidget(empty_label, 0, 1)
        record_button_layout.addWidget(empty_label, 0, 2)
        record_button_layout.addWidget(self.recording_label, 0, 3, alignment=Qt.AlignRight)
        record_button_layout.addWidget(self.record_stop_button, 0, 4)
        record_button_group_box.setLayout(record_button_layout)

        # layout
        layout = QVBoxLayout()
        layout.addWidget(fields_group_box)
        layout.addWidget(view_finder_group_box)
        layout.addWidget(record_button_group_box)
        self.setLayout(layout)

        # connect the record/stop button signal
        self.record_stop_button.clicked.connect(self.action_record_stop_button)

    @Slot()
    def action_record_stop_button(self):
        # check if the session name & video path file fields are filled
        if not self.session_name.text() or not self.video_file_path.text():
            self.error_dialog('Please inform both the Session Name and the Video/Audio Path!')
            return

        # check if the directory exists
        if not QDir(self.video_file_path.text()).exists():
            self.error_dialog('The directory {} does not exist!'.format(self.video_file_path.text()))
            return

        # check if the directory is writable
        if not os.access(self.video_file_path.text(), os.W_OK):
            self.error_dialog('The directory {} is not writable!'.format(self.video_file_path.text()))
            return

        if self.recording:
            # it is already recording
            # we will stop the session
            self.recording_label.setPixmap(self.ASSETS_IMAGES_FOLDER + 'gray_rec.png')
            self.record_stop_button.setText('Record session')
            # enable fields
            self.session_name.setEnabled(True)
            self.video_file_path.setEnabled(True)
            self.list_cameras.setEnabled(True)
            self.list_audio_devices.setEnabled(True)
            self.list_backing_tracks.setEnabled(True)
            # stop session
            self.record_session.stop()
            # restart camera
            if self.plat == 'Windows' or self.plat == 'Linux':
                self.wait_for_video_process()
        else:
            # it is not yet recording
            # we will start the session

            # on MacOs is possible to keep showing the camera
            # on GUI while it is recording the SAME camera.
            # Unfortunately, it is not possible neither on Linux
            # nor on Windows. This is the reason why we are
            # stopping the camera here and restarting it
            # after the recording is finished
            if self.plat == 'Windows' or self.plat == 'Linux':
                self.camera.stop()

            self.recording_label.setPixmap(self.ASSETS_IMAGES_FOLDER + 'red_rec.png')
            self.record_stop_button.setText('Recording… Press here to stop')
            # disable fields
            self.session_name.setEnabled(False)
            self.video_file_path.setEnabled(False)
            self.list_cameras.setEnabled(False)
            self.list_audio_devices.setEnabled(False)
            self.list_backing_tracks.setEnabled(False)
            # start session
            self.record_session.start_recording(self.session_name.text(),
                                                self.video_file_path.text())
        self.recording = not self.recording

    @Slot()
    def show_folder_browser(self):
        folder_dialog = QFileDialog()
        folder_dialog.setOption(QFileDialog.ShowDirsOnly)
        folder_dialog.setFileMode(QFileDialog.Directory)
        if folder_dialog.exec_():
            self.video_file_path.setText(folder_dialog.directory().absolutePath())

    @Slot()
    def refresh_audio_input(self):
        self.list_audio_devices.clear()
        self.get_list_audio_devices()

    @Slot()
    def change_backing_track(self):
        self.list_backing_tracks.clear()
        self.get_list_backing_tracks()

    @Slot()
    def refresh_cameras(self):
        self.list_cameras.clear()
        self.get_list_cameras()

    @Slot()
    def change_camera(self):
        self.camera.stop()
        self.camera = QCamera(self.list_cameras.currentData())
        self.camera.setCaptureMode(QCamera.CaptureVideo)
        self.start_camera()

    @Slot()
    def play_stop_backing_track(self):
        if self.backing_track_player.player.isPlaying():
            self.backing_track_player.stop()
            self.play_stop_backing_track_button.setText('Play backing track')
            # disable field
            self.list_backing_tracks.setEnabled(True)
        else:
            backing_track_file = '{}{}'.format(self.ASSETS_BACKING_AUDIO_FOLDER, self.list_backing_tracks.currentText())
            self.backing_track_player.play(backing_track_file)
            self.play_stop_backing_track_button.setText('Stop backing track')
            # enable field
            self.list_backing_tracks.setEnabled(False)

    def wait_for_video_process(self):
        loop = asyncio.get_event_loop()
        cors = asyncio.wait([self.check_video_process_terminate()])
        loop.run_until_complete(cors)

    async def check_video_process_terminate(self):
        while True:
            if self.record_session.check_status() is not None:
                break
        self.change_camera()


    def start_camera(self):
        self.camera.setViewfinder(self.view_finder)
        self.camera.start()

    def get_list_cameras(self):
        # list the available cameras
        for camera_info in QCameraInfo.availableCameras():
            # if 'Intel' not in camera_info.description():
            self.list_cameras.addItem(camera_info.description(), camera_info)

    def get_list_audio_devices(self):
        # list the available audio devices
        for device_info in QAudioDeviceInfo.availableDevices(QAudio.AudioInput):
            self.list_audio_devices.addItem(device_info.deviceName(), device_info)

    def get_list_backing_tracks(self):
        # list the available audio_backing tracks
        backing_tracks_folder = '{}*wav'.format(self.ASSETS_BACKING_AUDIO_FOLDER)
        for backing_track in glob(backing_tracks_folder):
            trackname = os.path.basename(backing_track)
            self.list_backing_tracks.addItem(trackname)

    def error_dialog(self, message):
        error_dialog = QMessageBox(self)
        error_dialog.setText(message)
        error_dialog.setWindowTitle('Blue Haze - Error')
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()

    # Threading Functions
    # Read data from buffer
    def brainbit_read(self):
        brainbit_data = self.brainbit.read()
        print('BrainBit data  =  ', brainbit_data)

    def brainbit_terminate(self):
        self.brainbit.terminate()

    # Read data from buffer
    def bitalino_read(self):
        # Read samples
        bitalino_data = self.bitalino.read(self.nSamples)
        print('BITalino data  =  ', bitalino_data)
        # Turn BITalino led on
        self.bitalino.trigger(self.digitalOutput)

    def bitalino_terminate(self):
        # Stop Bitalino acquisition
        self.bitalino.stop()
        # Close Bitalino connection
        self.bitalino.close()

    # Read data from buffer
    def skeleton_read(self):
        skeleton_data = self.skeleton.read()
        print('Skeleton data  =  ', skeleton_data)

    def skeleton_terminate(self):
        self.skeleton.terminate()

if __name__ == '__main__':
    # Initialise running vars
    running = True
    baudrate = 10 # Bitalino is 1, 10, 100, 1000

    # UI startup
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.setWindowTitle('Blue Haze')
    widget.setFixedSize(1350, 950)
    widget.show()

    # for i in range (100):
    #     print('Time  =  ', localtime())
    #     widget.brainbit_read()
    #     widget.bitalino_read()
    #     widget.skeleton_read()
    #     # control reading inline with project baudrate
    #     sleep(baudrate / 1000)
    #
    # # Terminations
    # widget.brainbit_terminate()
    # widget.bitalino_terminate()
    # widget.skeleton_terminate()

    # Close UI
    sys.exit(app.exec_())

