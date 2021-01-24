#
# Blue Haze
# 19 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

# todo: stop / terminate the hardware when the app closes
# todo: implement restart hardware button
# todo: slider

from PySide2.QtMultimedia import *
from PySide2.QtMultimediaWidgets import QCameraViewfinder
from PySide2.QtGui import QFont
from PySide2.QtCore import Qt, QDir
from glob import glob
from recordSession import RecordSession
from pathlib import Path
from feedback import *

import os
import sys
import asyncio
import nest_asyncio
import threading

import modules.utils as utls
import modules.config as cfg
import modules.ui as ui


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
        self.list_audio_devices.setDuplicatesEnabled(False)
        self.list_backing_tracks = QComboBox()
        self.PLAY_BACKING_TRACK = 'Play backing track'
        self.play_stop_backing_track_button = QPushButton(self.PLAY_BACKING_TRACK)

        # check if debug is on & auto set
        # session name & video file path fields
        if cfg.DEBUG:
            self.session_name.setText('test')
            self.video_file_path.setText(str(Path.home()) + '\Documents')

        # hardware
        self.bullet_bitalino_label = QLabel()
        self.bitalino_label = QLabel('Bitalino')
        self.bullet_brainbit_label = QLabel()
        self.brainbit_label = QLabel('Brainbit')
        self.bullet_realsense_label = QLabel()
        self.realsense_label = QLabel('RealSense camera')
        self.bullet_picoboard_label = QLabel()
        self.picoboard_label = QLabel('Picoboard')
        self.hardware_status = {'Bitalino': not cfg.HARDWARE,
                                'Brainbit': not cfg.HARDWARE,
                                'RealSense': not cfg.HARDWARE,
                                'Picoboard': not cfg.HARDWARE}

        # record bottom area
        self.record_stop_button = QPushButton('Record session')
        self.record_stop_button.setEnabled(not cfg.HARDWARE)
        self.recording_label = QLabel()

        # mic volume
        self.volume_slider = QSlider()
        self.volume_slider.setOrientation(Qt.Horizontal)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.setMinimum(1)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(cfg.UI_INITIAL_MIC_VOLUME)
        self.volume_slider.valueChanged.connect(self.change_value_mic_volume_label)
        self.volume_slider_label = QLabel('30')

        # states
        self.recording = False

        # objects
        self.backing_track_player = PlayAudioTrack(parent=self)
        self.view_finder = QCameraViewfinder()

        # hardware setup
        self.get_list_cameras()
        self.get_list_audio_devices()
        self.get_list_backing_tracks()

        if cfg.HARDWARE:
            self.setup_hw()

        # todo: DELETE!!!
        init_hardware = utls.Hardware(parent=self)
        threading.Thread(target=init_hardware.start_picoboard).start()

        # feedback
        self.feedback = Feedback()

        # ui setup
        self.setup_ui()

        # start the camera
        self.camera = QCamera(self.list_cameras.currentData())
        self.start_camera()

        # see
        # https://stackoverflow.com/questions/46827007/runtimeerror-this-event-loop-is-already-running-in-python
        nest_asyncio.apply()

        # record session object
        self.record_session = RecordSession(parent=self)

    def setup_hw(self):
        init_hardware = utls.Hardware(parent=self)

        # realsense, bitalino and brainbit init
        threading.Thread(target=init_hardware.start_realsense).start()
        threading.Thread(target=init_hardware.start_brainbit).start()
        threading.Thread(target=init_hardware.start_bitalino).start()
        threading.Thread(target=init_hardware.start_picoboard).start()

    def setup_ui(self):
        record_tab_widget = QWidget()
        record_tab_widget.setLayout(self.ui_tab_record_tab_widget())

        feedback_tab_widget = QWidget()
        feedback_tab_widget.setLayout(self.feedback.ui_tab_feedback_tab_widget())

        tab_widget = QTabWidget()
        tab_widget.addTab(record_tab_widget, 'Record')
        tab_widget.addTab(feedback_tab_widget, 'Feedback')
        tab_widget.currentChanged.connect(self.tab_changed)

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
        self.bullet_bitalino_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_idle.png')
        self.bullet_brainbit_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_idle.png')
        self.bullet_realsense_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_idle.png')
        self.bullet_picoboard_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_idle.png')

        refresh_hardware_button = QPushButton('Refresh hardware')

        hardware_list.addWidget(self.bullet_bitalino_label, 0, 0)
        hardware_list.addWidget(self.bitalino_label, 0, 1)
        hardware_list.addWidget(self.bullet_brainbit_label, 1, 0)
        hardware_list.addWidget(self.brainbit_label, 1, 1)
        hardware_list.addWidget(self.bullet_realsense_label, 2, 0)
        hardware_list.addWidget(self.realsense_label, 2, 1)
        hardware_list.addWidget(self.bullet_picoboard_label, 3, 0)
        hardware_list.addWidget(self.picoboard_label, 3, 1)
        hardware_list.addWidget(refresh_hardware_button, 4, 1, 2, 2)
        hardware_list.setRowStretch(5, 1)

        hardware_group_box.setLayout(hardware_list)

        fields_and_hardware.addWidget(fields_group_box, 0, 0)
        fields_and_hardware.addWidget(hardware_group_box, 0, 1)

        # viewfinder
        view_finder_group_box = QGroupBox()
        view_finder_group_box.setMinimumHeight(630)
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

    @Slot(dict)
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
            if self.backing_track_player.state() == QMediaPlayer.State.PlayingState:
                self.backing_track_player.stop()
            self.record_session.start_recording(self.session_name.text(),
                                                self.video_file_path.text(),
                                                self.list_cameras.currentData().description(),
                                                self.list_audio_devices.currentData(),
                                                self.list_backing_tracks.currentText(),
                                                int(self.volume_slider.value()))
        self.recording = not self.recording

    @Slot()
    def tab_changed(self, i):
        if i == 1:
            # to reload / update the list of collections in the feedback tab &
            # start the thread to read data from the picoboard
            self.feedback.get_list_sessions()
            self.feedback.start_thread_picoboard()
        else:
            # terminate the thread to read data from the picoboard
            # exit & quit simply don't work
            self.feedback.thread.terminate()

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
        if self.backing_track_player.state() == QMediaPlayer.State.PlayingState:
            self.backing_track_player.stop()
            self.play_stop_backing_track_button.setText(self.PLAY_BACKING_TRACK)
            # disable field
            self.list_backing_tracks.setEnabled(True)
        else:
            backing_track_file = '{}{}'.format(cfg.ASSETS_BACKING_AUDIO_FOLDER, self.list_backing_tracks.currentText())
            self.backing_track_player.setup_media(backing_track_file)
            self.backing_track_player.play()
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
                # extract audio from video
                self.record_session.extract_audio_from_video()
                break
        self.change_camera()

    def start_camera(self):
        self.camera.setViewfinder(self.view_finder)
        self.camera.start()

    def get_list_cameras(self):
        # list the available cameras
        for camera_info in QCameraInfo.availableCameras():
            # do not list RealSense Camera
            if 'Intel' not in camera_info.description():
                self.list_cameras.addItem(camera_info.description(), camera_info)

    def get_list_audio_devices(self):
        temp_list = []
        # list the available audio devices
        for device_info in QAudioDeviceInfo.availableDevices(QAudio.AudioInput):
            if device_info.deviceName() not in temp_list:
                self.list_audio_devices.addItem(device_info.deviceName(), device_info)
                temp_list.append(device_info.deviceName())

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

    # slot to get info from hardware initialization
    @Slot(dict)
    def hw_init_status(self, status):
        """
        status:
            : from : type of hardware
            : result :  True -> Ok
                        False -> Error
        """
        if status['result']:
            if status['from'] == 'RealSense':
                self.bullet_realsense_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_ok.png')
                self.realsense_label.setStyleSheet('QLabel { color: GreenYellow; }')
                self.hardware_status['RealSense'] = True
            elif status['from'] == 'Bitalino':
                self.bullet_bitalino_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_ok.png')
                self.bitalino_label.setStyleSheet('QLabel { color: GreenYellow; }')
                self.hardware_status['Bitalino'] = True
            elif status['from'] == 'BrainBit':
                self.bullet_brainbit_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_ok.png')
                self.brainbit_label.setStyleSheet('QLabel { color: GreenYellow; }')
                self.hardware_status['Brainbit'] = True
            elif status['from'] == 'Picoboard':
                self.bullet_picoboard_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_ok.png')
                self.picoboard_label.setStyleSheet('QLabel { color: GreenYellow; }')
                self.hardware_status['Picoboard'] = True
            if False not in self.hardware_status.values():
                self.record_stop_button.setEnabled(True)
        else:
            if status['from'] == 'RealSense':
                self.bullet_realsense_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_error.png')
                self.realsense_label.setStyleSheet('QLabel { color: red; }')
            elif status['from'] == 'Bitalino':
                self.bullet_bitalino_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_error.png')
                self.bitalino_label.setStyleSheet('QLabel { color: red; }')
            elif status['from'] == 'BrainBit':
                self.bullet_brainbit_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_error.png')
                self.brainbit_label.setStyleSheet('QLabel { color: red; }')
            elif status['from'] == 'Picoboard':
                self.bullet_picoboard_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'hardware_error.png')
                self.picoboard_label.setStyleSheet('QLabel { color: red; }')
            self.error_dialog('Error initializing {}. Please check the connections.'
                              .format(status['from']))

    Slot()
    def player_track_end(self):
        self.play_stop_backing_track_button.setText(self.PLAY_BACKING_TRACK)


if __name__ == '__main__':
    # UI startup
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    app = QApplication()

    # this is a workaround to prevent the font
    # from scaling up when the DPI is increased
    # for example, when using a 4K monitor
    # https://wiki.qt.io/Technical_FAQ#How_can_I_prevent_the_font_from_scaling_up_when_the_DPI_is_increased.3F
    # https://www.charlesodale.com/setting-qt-to-ignore-windows-dpi-text-size-personalization/
    # it is an ugly fix, as neither DisableHighDpiScaling nor EnableHighDpiScaling are working
    font = QFont()
    font.setPixelSize(13)
    app.setFont(font)

    app.setAttribute(Qt.AA_DontUseNativeDialogs)
    app.setStyle('Fusion')
    app.setPalette(ui.dark_palette())

    window = MainWindow()
    window.show()

    # Close UI
    sys.exit(app.exec_())
