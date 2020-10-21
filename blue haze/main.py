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
from PySide2.QtCore import Slot, Qt, QThread
from glob import glob
import os
import sys
from bitalino import BITalino
import argparse
import numpy as np
import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
import util as cm
import time
import pyrealsense2 as rs
import math
from skeletontracker import skeletontracker


# Bitalino setup parameters
# The macAddress variable on Windows can be "XX:XX:XX:XX:XX:XX" or "COMX"
# while on Mac OS can be "/dev/tty.BITalino-XX-XX-DevB" for devices ending with the last 4 digits of the MAC address or "/dev/tty.BITalino-DevB" for the remaining
bitalino_macAddress = "98:D3:B1:FD:3D:1F"

batteryThreshold = 30
acqChannels = [0] # removed , 1, 2, 3, 4, 5
samplingRate = 100 #100 hz all round
nSamples = 10
digitalOutput = [1, 1]


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.session_name = QLineEdit()
        self.video_file_path = QLineEdit()
        self.list_cameras = QComboBox()
        self.list_audio_devices = QComboBox()
        self.list_backing_tracks = QComboBox()
        self.record_stop_button = QPushButton('Record session')
        self.recording = False

        self.view_finder = QCameraViewfinder()

        self.get_list_cameras()
        self.get_list_audio_devices()
        self.get_list_backing_tracks()

        self.setup_ui()

        self.camera = QCamera(self.list_cameras.currentData())
        self.start_camera()

    def setup_ui(self):
        # fields
        fields_group_box = QGroupBox()
        fields = QGridLayout()
        fields.setSpacing(8)

        # session name
        session_name_label = QLabel('Session name: ')

        # video file path
        video_path_file_label = QLabel('Video path: ')
        folder_browser_button = QPushButton('Browse directories')
        # connect the button signal
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
        # connect the button signal
        refresh_audio_input_button.clicked.connect(self.refresh_audio_input)

        # backing track selection
        list_backing_tracks_label = QLabel('Available backing tracks: ')

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

        fields_group_box.setLayout(fields)

        # viewfinder
        view_finder_group_box = QGroupBox()
        view_finder_layout = QGridLayout()
        view_finder_layout.addWidget(self.view_finder, 1, 1)
        view_finder_group_box.setLayout(view_finder_layout)

        # record/stop button
        record_button_group_box = QGroupBox()
        record_button_layout = QGridLayout()
        # need to find a better solution
        # this is a workaround
        empty_label = QLabel(' ')
        record_button_layout.addWidget(empty_label, 0, 1)
        record_button_layout.addWidget(empty_label, 0, 2)
        record_button_layout.addWidget(empty_label, 0, 3)
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
        if self.recording:
            self.record_stop_button.setText('Record session')
        else:
            self.record_stop_button.setText('Recording…')
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
        self.start_camera()

    def start_camera(self):
        self.camera.setViewfinder(self.view_finder)
        self.camera.start()

    def get_list_cameras(self):
        # list the available cameras
        for camera_info in QCameraInfo.availableCameras():
            self.list_cameras.addItem(camera_info.description(), camera_info)

    def get_list_audio_devices(self):
        # list the available audio devices
        for device_info in QAudioDeviceInfo.availableDevices(QAudio.AudioInput):
            self.list_audio_devices.addItem(device_info.deviceName(), device_info)

    def get_list_backing_tracks(self):
        # list the available audio_backing tracks
        for backing_track in glob("../data/audio_backing/*wav"):
            trackname = os.path.basename(backing_track)
            self.list_backing_tracks.addItem(trackname)

class BitalinoReader(BITalino):
    def __init__(self):
        # Connect to BITalino
        self.device = BITalino(bitalino_macAddress)

        # Set battery threshold
        self.device.battery(batteryThreshold)

        # Read BITalino version
        print(self.device.version())

    def read(self):
        # Start Acquisition
        self.device.start(samplingRate, acqChannels)

        # Read samples
        print(self.device.read(nSamples))

        # Turn BITalino led on
        self.device.trigger(digitalOutput)

    def terminate(self):
        # Stop Bitalino acquisition
        self.device.stop()

        # Close Bitalino connection
        self.device.close()


class BrainbitReader():
    def __init__(self):
        # self.parser = argparse.ArgumentParser()
        # # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port
        # self.parser.add_argument ('--timeout', type = int, help  = 'timeout for device discovery or connection', required = False, default = 0)
        # self.parser.add_argument ('--ip-port', type = int, help  = 'ip port', required = False, default = 0)
        # self.parser.add_argument ('--ip-protocol', type = int, help  = 'ip protocol, check IpProtocolType enum', required = False, default = 0)
        # self.parser.add_argument ('--ip-address', type = str, help  = 'ip address', required = False, default = '')
        # self.parser.add_argument ('--serial-port', type = str, help  = 'serial port', required = False, default = '')
        # self.parser.add_argument ('--mac-address', type = str, help  = 'mac address', required = False, default = '')
        # self.parser.add_argument ('--other-info', type = str, help  = 'other info', required = False, default = '')
        # self.parser.add_argument ('--streamer-params', type = str, help  = 'streamer params', required = False, default = '')
        # self.parser.add_argument ('--serial-number', type = str, help  = 'serial number', required = False, default = '')
        # self.parser.add_argument ('--board-id', type = int, help  = 'board id, check docs to get a list of supported boards', required = False, default=7)
        # self.parser.add_argument ('--file', type = str, help  = 'file', required = False, default = '')
        # self.parser.add_argument ('--log', action = 'store_true')
        # self.args = self.parser.parse_args ()

        self.params = BrainFlowInputParams ()
        self.params.ip_port = 0
        self.params.serial_port = ''
        self.params.mac_address = ''
        self.params.other_info = ''
        self.params.serial_number = ''
        self.params.ip_address = ''
        self.params.ip_protocol = 0
        self.params.timeout = 0
        self.params.file = 0

        if (self.args.log):
            BoardShim.enable_dev_board_logger ()
        else:
            BoardShim.disable_board_logger ()

        self.board = BoardShim (self.args.board_id, self.params)

        self.board.prepare_session ()

        # board.start_stream () # use this for default options
        self.board.start_stream(45000, self.args.streamer_params)

    def read(self):
        # data = board.get_current_board_data (256) # get latest 256 packages or less, doesnt remove them from internal buffer
        self.data = self.board.get_board_data () # get all data and remove it from internal buffer
        print (self.data)

    def terminate(self):
        self.board.stop_stream()
        self.board.release_session()


class SkeletonReader():
    def __init__(self):
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)

        # Start the realsense pipeline
        self.pipeline = rs.pipeline()
        self.pipeline.start()

        # Create align object to align depth frames to color frames
        self.align = rs.align(rs.stream.color)

        # Get the intrinsics information for calculation of 3D point
        self.unaligned_frames = pipeline.wait_for_frames()
        self.frames = self.align.process(self.unaligned_frames)
        self.depth = self.frames.get_depth_frame()
        self.depth_intrinsic = self.depth.profile.as_video_stream_profile().intrinsics

        # Initialize the cubemos api with a valid license key in default_license_dir()
        self.skeletrack = skeletontracker(cloud_tracking_api_key="")
        self.joint_confidence = 0.2


    def read(self):
        # Create a pipeline object. This object configures the streaming camera and owns it's handle
        self.unaligned_frames = self.pipeline.wait_for_frames()
        self.frames = self.align.process(self.unaligned_frames)
        self.depth = self.frames.get_depth_frame()
        self.color = self.frames.get_color_frame()
        # if not self.depth or not self.color:
        #     continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(self.depth.get_data())
        color_image = np.asanyarray(self.color.get_data())

        # perform inference and update the tracking id
        self.skeletons = self.skeletrack.track_skeletons(color_image)

        # print (color_image, self.skeletons, self.depth, self.depth_intrinsic, self.joint_confidence)

        # # render the skeletons on top of the acquired image and display it
        # color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        # cm.render_result(skeletons, color_image, joint_confidence)
        # render_ids_3d(
        #     color_image, skeletons, depth, depth_intrinsic, joint_confidence
        # )
        # cv2.imshow(window_name, color_image)
        # if cv2.waitKey(1) == 27:
        #     break

    def terminate(self):
        self.pipeline.stop()

if __name__ == '__main__':
    running = True
    # BITalino startup
    bitalino = BitalinoReader()

    #BraibBit startup
    brainbit = BrainbitReader()

    # RealSense & Skeleton startup
    skeleton = SkeletonReader()

    # UI startup
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.setWindowTitle('Blue Haze')
    widget.setFixedSize(1350, 950)
    widget.show()


    #Terminations
    if not running:
        brainbit.terminate()
        bitalino.terminate()
        skeleton.terminate()

        # Close UI
        sys.exit(app.exec_())