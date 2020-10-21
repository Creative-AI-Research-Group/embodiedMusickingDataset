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

def bitalino_setup():
    # Connect to BITalino
    device = BITalino(bitalino_macAddress)

    # Set battery threshold
    device.battery(batteryThreshold)

    # Read BITalino version
    print(device.version())

    return device

def bitalino_read():
    # Start Acquisition
    device.start(samplingRate, acqChannels)

    # Read samples
    print(device.read(nSamples))

    # Turn BITalino led on
    device.trigger(digitalOutput)

def bitalino_terminate():
    # Stop Bitalino acquisition
    device.stop()

    # Close Bitalino connection
    device.close()


def brainbit_setup ():
    parser = argparse.ArgumentParser()
    # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port
    parser.add_argument ('--timeout', type = int, help  = 'timeout for device discovery or connection', required = False, default = 0)
    parser.add_argument ('--ip-port', type = int, help  = 'ip port', required = False, default = 0)
    parser.add_argument ('--ip-protocol', type = int, help  = 'ip protocol, check IpProtocolType enum', required = False, default = 0)
    parser.add_argument ('--ip-address', type = str, help  = 'ip address', required = False, default = '')
    parser.add_argument ('--serial-port', type = str, help  = 'serial port', required = False, default = '')
    parser.add_argument ('--mac-address', type = str, help  = 'mac address', required = False, default = '')
    parser.add_argument ('--other-info', type = str, help  = 'other info', required = False, default = '')
    parser.add_argument ('--streamer-params', type = str, help  = 'streamer params', required = False, default = '')
    parser.add_argument ('--serial-number', type = str, help  = 'serial number', required = False, default = '')
    parser.add_argument ('--board-id', type = int, help  = 'board id, check docs to get a list of supported boards', required = False, default=7)
    parser.add_argument ('--file', type = str, help  = 'file', required = False, default = '')
    parser.add_argument ('--log', action = 'store_true')
    args = parser.parse_args ()

    params = BrainFlowInputParams ()
    params.ip_port = args.ip_port
    params.serial_port = args.serial_port
    params.mac_address = args.mac_address
    params.other_info = args.other_info
    params.serial_number = args.serial_number
    params.ip_address = args.ip_address
    params.ip_protocol = args.ip_protocol
    params.timeout = args.timeout
    params.file = args.file

    if (args.log):
        BoardShim.enable_dev_board_logger ()
    else:
        BoardShim.disable_board_logger ()

    board = BoardShim (args.board_id, params)

    board.prepare_session ()

    # board.start_stream () # use this for default options
    board.start_stream(45000, args.streamer_params)

    return board, args

def brainbit_read(board):
    # data = board.get_current_board_data (256) # get latest 256 packages or less, doesnt remove them from internal buffer
    data = board.get_board_data () # get all data and remove it from internal buffer
    print (data)

def brainbit_terminate():
    board.stop_stream()
    board.release_session()

def render_ids_3d(
    render_image, skeletons_2d, depth_map, depth_intrinsic, joint_confidence
):
    thickness = 1
    text_color = (255, 255, 255)
    rows, cols, channel = render_image.shape[:3]
    distance_kernel_size = 5
    # calculate 3D keypoints and display them
    for skeleton_index in range(len(skeletons_2d)):
        skeleton_2D = skeletons_2d[skeleton_index]
        joints_2D = skeleton_2D.joints
        did_once = False
        for joint_index in range(len(joints_2D)):
            if did_once == False:
                cv2.putText(
                    render_image,
                    "id: " + str(skeleton_2D.id),
                    (int(joints_2D[joint_index].x), int(joints_2D[joint_index].y - 30)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    text_color,
                    thickness,
                )
                did_once = True
            # check if the joint was detected and has valid coordinate
            if skeleton_2D.confidences[joint_index] > joint_confidence:
                distance_in_kernel = []
                low_bound_x = max(
                    0,
                    int(
                        joints_2D[joint_index].x - math.floor(distance_kernel_size / 2)
                    ),
                )
                upper_bound_x = min(
                    cols - 1,
                    int(joints_2D[joint_index].x + math.ceil(distance_kernel_size / 2)),
                )
                low_bound_y = max(
                    0,
                    int(
                        joints_2D[joint_index].y - math.floor(distance_kernel_size / 2)
                    ),
                )
                upper_bound_y = min(
                    rows - 1,
                    int(joints_2D[joint_index].y + math.ceil(distance_kernel_size / 2)),
                )
                for x in range(low_bound_x, upper_bound_x):
                    for y in range(low_bound_y, upper_bound_y):
                        distance_in_kernel.append(depth_map.get_distance(x, y))
                median_distance = np.percentile(np.array(distance_in_kernel), 50)
                depth_pixel = [
                    int(joints_2D[joint_index].x),
                    int(joints_2D[joint_index].y),
                ]
                if median_distance >= 0.3:
                    point_3d = rs.rs2_deproject_pixel_to_point(
                        depth_intrinsic, depth_pixel, median_distance
                    )
                    point_3d = np.round([float(i) for i in point_3d], 3)
                    point_str = [str(x) for x in point_3d]
                    cv2.putText(
                        render_image,
                        str(point_3d),
                        (int(joints_2D[joint_index].x), int(joints_2D[joint_index].y)),
                        cv2.FONT_HERSHEY_DUPLEX,
                        0.4,
                        text_color,
                        thickness,
                    )

def skeleton_setup():
    config = rs.config()
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)

    # Start the realsense pipeline
    pipeline = rs.pipeline()
    pipeline.start()

    # Create align object to align depth frames to color frames
    align = rs.align(rs.stream.color)

    # Get the intrinsics information for calculation of 3D point
    unaligned_frames = pipeline.wait_for_frames()
    frames = align.process(unaligned_frames)
    depth = frames.get_depth_frame()
    depth_intrinsic = depth.profile.as_video_stream_profile().intrinsics

    # Initialize the cubemos api with a valid license key in default_license_dir()
    skeletrack = skeletontracker(cloud_tracking_api_key="")
    joint_confidence = 0.2

    return pipeline, skeletrack, joint_confidence

def skeleton_read(pipeline, skeletrack, joint_confidence):
    while True:
        # Create a pipeline object. This object configures the streaming camera and owns it's handle
        unaligned_frames = pipeline.wait_for_frames()
        frames = align.process(unaligned_frames)
        depth = frames.get_depth_frame()
        color = frames.get_color_frame()
        if not depth or not color:
            continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth.get_data())
        color_image = np.asanyarray(color.get_data())

        # perform inference and update the tracking id
        skeletons = skeletrack.track_skeletons(color_image)

        # render the skeletons on top of the acquired image and display it
        color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        cm.render_result(skeletons, color_image, joint_confidence)
        render_ids_3d(
            color_image, skeletons, depth, depth_intrinsic, joint_confidence
        )
        cv2.imshow(window_name, color_image)
        if cv2.waitKey(1) == 27:
            break

def skeleton_terminate():
    pipeline.stop()

if __name__ == '__main__':
    # BITalino startup
    device = bitalino_setup()

    #BraibBit startup
    board, args = brainbit_setup()

    # RealSense & Skeleton startup
    pipeline, skeletrack, joint_confidence = skeleton_setup()

    # UI startup
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.setWindowTitle('Blue Haze')
    widget.setFixedSize(1350, 950)
    widget.show()


    #Terminations

    brainbit_terminate()
    bitalino_terminate()
    skeleton_terminate()

    # Close UI
    sys.exit(app.exec_())