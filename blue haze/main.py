#
# Blue Haze
# 19 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

# todo: fix the backtrack button status when playing
# todo: 'unduplicate' audio inputs
# todo: autostop of 3-5 seconds following backing track end
# todo: insert field in UI for input of audio record level (1-100)
# todo: add timestamp delta between ts(n) and ts(n-1)

from PySide2.QtWidgets import *
from PySide2.QtMultimedia import *
from PySide2.QtMultimediaWidgets import QCameraViewfinder
from PySide2.QtGui import QPalette, QColor
from PySide2.QtCore import Slot, Qt, QDir
from glob import glob
from playBackTrack import PlayBackTrack
from recordSession import RecordSession

import os
import sys
import asyncio
import nest_asyncio

import modules.utils as utls
import modules.config as cfg


def dark_palette():
    # dark theme
    dark_palette_colours = QPalette()
    dark_palette_colours.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette_colours.setColor(QPalette.WindowText, Qt.white)
    dark_palette_colours.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette_colours.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette_colours.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette_colours.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette_colours.setColor(QPalette.Text, Qt.white)
    dark_palette_colours.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette_colours.setColor(QPalette.ButtonText, Qt.white)
    dark_palette_colours.setColor(QPalette.BrightText, Qt.red)
    dark_palette_colours.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette_colours.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette_colours.setColor(QPalette.HighlightedText, Qt.black)
    return dark_palette_colours


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # window basic properties
        self.setWindowTitle('Blue Haze')
        self.setFixedSize(cfg.UI_WIDTH, cfg.UI_HEIGHT)

        # setup group
        self.session_name = QLineEdit()
        self.video_file_path = QLineEdit()
        self.list_cameras = QComboBox()
        self.list_audio_devices = QComboBox()
        self.list_backing_tracks = QComboBox()
        self.play_stop_backing_track_button = QPushButton('Play backing track')

        # record bottom area
        self.record_stop_button = QPushButton('Record session')
        self.recording_label = QLabel()

        # mic volume
        self.volume_slider = QSlider()
        self.volume_slider.setOrientation(Qt.Horizontal)
        self.volume_slider.setTickInterval(1)
        self.volume_slider.setMinimum(1)
        self.volume_slider.setMaximum(10)
        self.volume_slider.setValue(cfg.UI_INITIAL_MIC_VOLUME)
        self.volume_slider.valueChanged.connect(self.change_value_mic_volume_label)
        self.volume_slider_label = QLabel('3')

        # objects
        self.backing_track_player = PlayBackTrack()
        self.record_session = RecordSession()
        self.view_finder = QCameraViewfinder()

        # states
        self.recording = False

        # hardware setup
        self.get_list_cameras()
        self.get_list_audio_devices()
        self.get_list_backing_tracks()

        # ui setup
        self.setup_ui()

        # start the camera
        self.camera = QCamera(self.list_cameras.currentData())
        self.start_camera()

        # see
        # https://stackoverflow.com/questions/46827007/runtimeerror-this-event-loop-is-already-running-in-python
        nest_asyncio.apply()

    def setup_ui(self):
        record_tab_widget = QWidget()
        record_tab_widget.setLayout(self.ui_tab_record_tab_widget())

        edit_tab_widget = QWidget()

        feedback_tab_widget = QWidget()

        tab_widget = QTabWidget()
        tab_widget.addTab(record_tab_widget, 'Record')
        tab_widget.addTab(edit_tab_widget, 'Edit')
        tab_widget.addTab(feedback_tab_widget, 'Feedback')

        # disable Edit & Feedback for now
        tab_widget.setTabEnabled(1, False)
        tab_widget.setTabEnabled(2, False)

        # let's add some margin/breathing space to it!
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 25, 20, 20)
        main_layout.addWidget(tab_widget)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # connect the record/stop button signal
        self.record_stop_button.clicked.connect(self.action_record_stop_button)

    def ui_tab_record_tab_widget(self):
        # fields & hardware
        fields_and_hardware = QGridLayout()

        # hardware
        hardware_group_box = QGroupBox()
        hardware_list = QGridLayout()
        hardware_list.setSpacing(5)

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

        # mic volume slider
        mic_volume_slider_label = QLabel('Mic volume: ')

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

        # mic volume slider
        fields.addWidget(mic_volume_slider_label, 5, 0)
        fields.addWidget(self.volume_slider, 5, 1)
        fields.addWidget(self.volume_slider_label, 5, 2)

        fields_group_box.setLayout(fields)

        # hardware
        bullet_bitalino_label = QLabel()
        bullet_bitalino_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_idle.png')
        bitalino_label = QLabel('Bitalino')

        bullet_brainbit_label = QLabel()
        bullet_brainbit_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_idle.png')
        brainbit_label = QLabel('Brainbit')

        bullet_realsense_label = QLabel()
        bullet_realsense_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_idle.png')
        realsense_label = QLabel('RealSense camera')

        refresh_hardware_button = QPushButton('Refresh hardware')

        hardware_list.addWidget(bullet_bitalino_label, 0, 0)
        hardware_list.addWidget(bitalino_label, 0, 1)
        hardware_list.addWidget(bullet_brainbit_label, 1, 0)
        hardware_list.addWidget(brainbit_label, 1, 1)
        hardware_list.addWidget(bullet_realsense_label, 2, 0)
        hardware_list.addWidget(realsense_label, 2, 1)
        hardware_list.addWidget(refresh_hardware_button, 3, 1, 2, 2)
        hardware_list.setRowStretch(4, 1)

        hardware_group_box.setLayout(hardware_list)

        fields_and_hardware.addWidget(fields_group_box, 0, 0)
        fields_and_hardware.addWidget(hardware_group_box, 0, 1)

        # viewfinder
        view_finder_group_box = QGroupBox()
        view_finder_layout = QGridLayout()
        view_finder_layout.addWidget(self.view_finder, 1, 1)
        view_finder_group_box.setLayout(view_finder_layout)

        # record/stop button
        record_button_group_box = QGroupBox()
        record_button_layout = QHBoxLayout()

        # rec image
        self.recording_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'gray_rec.png')
        record_button_layout.addStretch(1)
        record_button_layout.addWidget(self.recording_label)
        record_button_layout.addWidget(self.record_stop_button)
        record_button_group_box.setLayout(record_button_layout)

        # layout
        record_tab_layout = QVBoxLayout()
        record_tab_layout.addLayout(fields_and_hardware)
        record_tab_layout.addWidget(view_finder_group_box)
        record_tab_layout.addWidget(record_button_group_box)

        return record_tab_layout

    def change_value_mic_volume_label(self):
        self.volume_slider_label.setText(str(self.volume_slider.value()))

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
            self.recording_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'gray_rec.png')
            self.record_stop_button.setText('Record session')
            # enable fields
            self.session_name.setEnabled(True)
            self.video_file_path.setEnabled(True)
            self.list_cameras.setEnabled(True)
            self.list_audio_devices.setEnabled(True)
            self.list_backing_tracks.setEnabled(True)
            self.volume_slider.setEnabled(True)
            # stop session
            self.record_session.stop()
            # restart camera
            self.wait_for_video_process()
        else:
            # it is not yet recording
            # we will start the session

            # on MacOs it is possible to keep showing the camera
            # on GUI while it is recording the SAME camera.
            # Unfortunately, it is not possible neither on Linux
            # nor on Windows. This is the reason why we are
            # stopping the camera here and restarting it
            # after the recording is finished
            self.camera.stop()

            self.recording_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'red_rec.png')
            self.record_stop_button.setText('Recording… Press here to stop')
            # disable fields
            self.session_name.setEnabled(False)
            self.video_file_path.setEnabled(False)
            self.list_cameras.setEnabled(False)
            self.list_audio_devices.setEnabled(False)
            self.list_backing_tracks.setEnabled(False)
            self.volume_slider.setEnabled(False)
            # start session
            if self.backing_track_player.player.isPlaying():
                self.backing_track_player.stop()
                self.backing_track_player.player.isPlaying = False
            self.record_session.start_recording(self.session_name.text(),
                                                self.video_file_path.text(),
                                                self.list_cameras.currentData().description(),
                                                self.list_audio_devices.currentData(),
                                                self.list_backing_tracks.currentText())
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
            backing_track_file = '{}{}'.format(cfg.ASSETS_BACKING_AUDIO_FOLDER, self.list_backing_tracks.currentText())
            self.backing_track_player.play(backing_track_file)
            self.play_stop_backing_track_button.setText('Stop backing track')
            # enable field
            self.list_backing_tracks.setEnabled(False)

    def wait_for_video_process(self):
        loop = asyncio.get_event_loop()
        async_function = asyncio.wait([self.check_video_process_terminate()])
        loop.run_until_complete(async_function)

    async def check_video_process_terminate(self):
        while True:
            if self.record_session.video_process.poll() is not None:
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
        backing_tracks_folder = '{}*wav'.format(cfg.ASSETS_BACKING_AUDIO_FOLDER)
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


if __name__ == '__main__':
    # UI startup
    app = QApplication()
    app.setStyle('Fusion')
    app.setPalette(dark_palette())

    window = MainWindow()
    window.show()

    # Close UI
    sys.exit(app.exec_())
