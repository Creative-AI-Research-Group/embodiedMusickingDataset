#
# Blue Haze
# 11 Jan 2021
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

import os

import matplotlib

import modules.config as cfg
import modules.ui as ui
import modules.utils as utls

from PySide2.QtWidgets import *
from PySide2.QtGui import QIcon
from PySide2.QtCore import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from scipy.io import wavfile

from time import sleep
from subprocess import Popen

from database import *
from playAudioTrack import PlayAudioTrack


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):

        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor('#424242')

        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor('#424242')
        self.axes.get_yaxis().set_visible(False)
        self.axes.get_xaxis().set_visible(False)
        super(MplCanvas, self).__init__(fig)


class ThreadToReadPicoboardSignals(QObject):
    finished = Signal(int)


class ThreadToReadPicoboard(QThread):
    def __init__(self, hardware, parent=None):
        QThread.__init__(self, parent)
        self.signal = ThreadToReadPicoboardSignals()
        self.hardware = hardware

    def run(self):
        while True:
            try:
                flow_level = self.hardware.read_picoboard()
                self.signal.finished.emit(flow_level)
                sleep(cfg.BITALINO_BAUDRATE / 1000)
            except RuntimeError:
                # all the C++ objects have been already deleted
                pass


class Feedback(QWidget, QObject):
    def __init__(self, parent=None):
        super().__init__()

        if parent is not None:
            self.enable_disable_recording_tab = utls.EmitSignal(parent, parent.enable_disable_recording_tab)

        # setup matplotlib to use Qt5
        matplotlib.use('Qt5Agg')

        # database object
        self.database = Database()
        self.last_position = 0

        # player object
        self.player = PlayAudioTrack(parent=self)

        # picoboard
        hardware = utls.Hardware()

        # thread
        self.thread = ThreadToReadPicoboard(hardware)

        # audio file name
        self.audio_file_name = None

        # constants
        # icons
        self.PAUSE_GRAY = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_pause.png')
        self.PAUSE_RED = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'red_pause.png')
        self.PLAY_GRAY = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_play.png')
        self.PLAY_RED = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'red_play.png')
        self.RECORD_GRAY = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_record.png')
        self.RECORD_RED = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'red_record.png')
        self.STOP_GRAY = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_stop.png')
        self.STOP_RED = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'red_stop.png')

        # player states
        self.PAUSED = self.player.State.PausedState
        self.PLAYING = self.player.State.PlayingState
        self.STOPPED = self.player.State.StoppedState

        '''
            [0] -> pause button
            [1] -> play button
            [2] -> record button
            [3] -> stop button
        '''
        self.actual_icons = [self.PAUSE_GRAY,
                             self.PLAY_GRAY,
                             self.RECORD_GRAY,
                             self.STOP_GRAY]

        # list of sessions
        self.session_name_feedback_tab = QComboBox()
        self.session_name_feedback_tab.setDuplicatesEnabled(False)
        self.session_name_feedback_tab.activated[str].connect(self.change_session)

        # session name
        self.session_to_edit_name = QLabel('Session: ')

        # player buttons
        self.pause_player_button = QPushButton()
        self.play_player_button = QPushButton()
        self.record_player_button = QPushButton()
        self.stop_player_button = QPushButton()
        self.set_buttons()
        self.feedback_session = False

        # position slider
        # style sheet
        position_slider_style_sheet = """
                .QSlider {
                    min-height: 45px;
                    max-height: 45px;
                }
                
                .QSlider::groove:horizontal {
                    height: 25px;
                    background: #393939;
                }
                
                .QSlider::sub-page:horizontal {
                    background: #CCCCCC;
                }
                
        """
        self.position_slider = QSlider()
        self.position_slider.setOrientation(Qt.Horizontal)
        self.position_slider.setStyleSheet(position_slider_style_sheet)
        self.position_slider.setMinimum(1)
        self.position_slider.setMaximum(100)
        self.position_slider.setValue(0)
        self.position_slider.setEnabled(False)

        # progress bar / feedback bar
        self.feedback_bar = QProgressBar()
        self.feedback_bar.setMinimum(0)
        self.feedback_bar.setMaximum(100)
        self.old_flow_level = 0

        # spectrogram
        self.spectrogram = MplCanvas(self, width=10, height=15, dpi=100)
        self.spectrogram.axes.get_yaxis().set_visible(False)
        self.spectrogram.axes.get_xaxis().set_visible(False)
        self.spectrogram.axes.axis('off')

    def setup(self, current_session):
        self.get_list_sessions()
        if current_session is not None:
            idx = self.session_name_feedback_tab.findText(current_session)
            if idx != -1:
                self.session_name_feedback_tab.setCurrentIndex(idx)
        self.start_thread_picoboard()
        self.change_session()

    def change_session(self):
        try:
            self.show_hide_sessions_names(True)
            self.audio_file_name = self.database.get_audio_file_name(self.session_name_feedback_tab.currentText())
            self.generate_spectrogram()
        except Exception as err:
            utls.logger.error(err)
            # empty database
            self.show_hide_sessions_names(False)

    def show_hide_sessions_names(self, show_sessions_names=True):
        ERROR_MESSAGE = 'ERROR: Could not find any records in the database'
        if show_sessions_names:
            self.enable_disable_buttons(False, True)
            self.session_name_feedback_tab.show()
            self.session_to_edit_name.setText('Session: ')
        else:
            self.enable_disable_buttons(False, False)
            self.session_name_feedback_tab.hide()
            self.session_to_edit_name.setText(ERROR_MESSAGE)
            ui.MessageBox('Blue Haze - Error', ERROR_MESSAGE, ui.MessageBox.Warning).exec_()

    def set_buttons(self):
        style_sheet = """
                            QPushButton {
                                background-color: none;
                                border: none;
                            }
                    """

        # player buttons
        self.pause_player_button.setIconSize(QSize(54, 54))
        self.pause_player_button.setStyleSheet(style_sheet)
        self.pause_player_button.installEventFilter(self)
        self.pause_player_button.clicked.connect(self.pause)

        self.play_player_button.setIconSize(QSize(68, 68))
        self.play_player_button.setStyleSheet(style_sheet)
        self.play_player_button.installEventFilter(self)
        self.play_player_button.clicked.connect(self.play)

        self.record_player_button.setIconSize(QSize(68, 68))
        self.record_player_button.setStyleSheet(style_sheet)
        self.record_player_button.installEventFilter(self)
        self.record_player_button.clicked.connect(self.start_stop_feedback)

        self.stop_player_button.setIconSize(QSize(54, 54))
        self.stop_player_button.setStyleSheet(style_sheet)
        self.stop_player_button.installEventFilter(self)
        self.stop_player_button.clicked.connect(self.stop)

        # set icons
        self.update_icons()

        # disable the pause & stop buttons
        self.enable_disable_buttons(False)

    def ui_tab_feedback_tab_widget(self):
        # session field
        session_to_edit = QGridLayout()
        session_to_edit_group_box = QGroupBox()
        session_to_edit_layout = QGridLayout()
        session_to_edit_layout.setSpacing(8)

        # fields layout
        session_to_edit_layout.addWidget(self.session_to_edit_name, 0, 1)
        session_to_edit_layout.addWidget(self.session_name_feedback_tab, 0, 2)
        session_to_edit_layout.setColumnStretch(3, 1)

        session_to_edit_group_box.setLayout(session_to_edit_layout)
        session_to_edit.addWidget(session_to_edit_group_box)

        # spectrogram
        spectrogram_group_box = QGroupBox()
        spectrogram_layout = QGridLayout()
        spectrogram_layout.addWidget(self.spectrogram, 0, 0)
        spectrogram_group_box.setLayout(spectrogram_layout)

        # position slider
        position_slider_group_box = QGroupBox()
        position_slider_layout = QGridLayout()
        position_slider_layout.setContentsMargins(200, 0, 170, 0)
        position_slider_layout.addWidget(self.position_slider, 2, 1)
        position_slider_group_box.setLayout(position_slider_layout)

        # player
        player_group_box = QGroupBox()
        player_layout = QGridLayout()
        player_layout.setSpacing(20)
        player_layout.addWidget(self.pause_player_button, 2, 1)
        player_layout.addWidget(self.play_player_button, 2, 2)
        player_layout.addWidget(self.record_player_button, 2, 3)
        player_layout.addWidget(self.stop_player_button, 2, 4)
        player_layout.setColumnStretch(0, 1)
        player_layout.setColumnStretch(5, 1)
        player_group_box.setLayout(player_layout)

        # progress bar / feedback bar
        feedback_bar_group_box = QGroupBox()
        feedback_bar_layout = QGridLayout()
        feedback_bar_label = QLabel('Flow level: ')
        feedback_bar_layout.addWidget(feedback_bar_label, 0, 0)
        feedback_bar_layout.addWidget(self.feedback_bar, 0, 1)
        feedback_bar_group_box.setLayout(feedback_bar_layout)

        # layout
        session_tab_layout = QVBoxLayout()
        session_tab_layout.addLayout(session_to_edit)
        session_tab_layout.addWidget(spectrogram_group_box)
        session_tab_layout.addWidget(position_slider_group_box)
        session_tab_layout.addWidget(player_group_box)
        session_tab_layout.addWidget(feedback_bar_group_box)

        return session_tab_layout

    @Slot(int)
    def picoboard_thread_complete(self, flow):
        if self.player.state() is self.PLAYING:
            self.position_slider.setMaximum(self.player.duration())
            self.position_slider.setValue(self.player.position())
        if self.old_flow_level != flow:
            self.feedback_bar.setValue(flow)
            if self.feedback_session and self.player.state() is not self.PAUSED:
                # update MongoDB
                actual_position = self.player.position()
                self.database.update_fields(self.session_name_feedback_tab.currentText(),
                                            self.old_flow_level,
                                            flow,
                                            self.last_position,
                                            actual_position)
                self.last_position = actual_position
            self.old_flow_level = flow

    def start_thread_picoboard(self):
        self.thread.signal.finished.connect(self.picoboard_thread_complete)
        self.thread.start()

    def get_list_sessions(self):
        collections = self.database.list_sessions()

        # clear the list to avoid duplicates
        self.session_name_feedback_tab.clear()

        for collection_name in collections:
            self.session_name_feedback_tab.addItem(collection_name)

    def play(self):
        # enable the other buttons
        self.enable_disable_buttons(True)

        # check if the player is not paused
        if self.player.state() is not self.PAUSED:
            self.player.setup_media(self.audio_file_name)

        self.player.play()

    def stop(self):
        self.player.stop()

        # reset the buttons
        self.player_track_end()

    def enable_disable_buttons(self, state_pause_stop=None, state_play_record=None):
        if state_pause_stop is not None:
            self.pause_player_button.setEnabled(state_pause_stop)
            self.stop_player_button.setEnabled(state_pause_stop)
        elif state_play_record is not None:
            self.play_player_button.setEnabled(state_play_record)
            self.record_player_button.setEnabled(state_play_record)

    def pause(self):
        # check if the player is already paused
        if self.player.state() is self.PAUSED:
            self.player.play()
        else:
            self.player.pause()

    def eventFilter(self, obj, event):
        # this is a bit messy and should be improved
        try:
            current_state = self.player.state()
        except RuntimeError:
            # all the C++ objects have been already deleted
            pass
        if event.type() is QEvent.HoverEnter:
            if obj is self.pause_player_button and current_state is not self.PAUSED:
                self.actual_icons[0] = self.PAUSE_RED
            elif obj is self.play_player_button and current_state is not self.PLAYING:
                self.actual_icons[1] = self.PLAY_RED
            elif obj is self.record_player_button:
                self.actual_icons[2] = self.RECORD_RED
            elif obj is self.stop_player_button:
                self.actual_icons[3] = self.STOP_RED
        elif event.type() is QEvent.HoverLeave:
            if obj is self.pause_player_button and current_state is not self.PAUSED:
                self.actual_icons[0] = self.PAUSE_GRAY
            elif obj is self.play_player_button and current_state is not self.PLAYING:
                self.actual_icons[1] = self.PLAY_GRAY
            elif obj is self.record_player_button and not self.feedback_session:
                self.actual_icons[2] = self.RECORD_GRAY
            elif obj is self.stop_player_button:
                self.actual_icons[3] = self.STOP_GRAY
        elif event.type() is QEvent.MouseButtonPress:
            if obj is self.play_player_button:
                if not self.feedback_session:
                    self.actual_icons[0] = self.PAUSE_GRAY
                    self.actual_icons[1] = self.PLAY_RED
            elif obj is self.pause_player_button:
                if current_state is self.PAUSED:
                    self.actual_icons[0] = self.PAUSE_GRAY
                    if self.feedback_session:
                        self.actual_icons[2] = self.RECORD_RED
                    else:
                        self.actual_icons[1] = self.PLAY_RED
                else:
                    self.actual_icons[0] = self.PAUSE_RED
                    self.actual_icons[1] = self.PLAY_GRAY
                    self.actual_icons[2] = self.RECORD_GRAY
            elif obj is self.stop_player_button:
                self.actual_icons[0] = self.PAUSE_GRAY
                self.actual_icons[1] = self.PLAY_GRAY
                self.actual_icons[2] = self.RECORD_GRAY
                if self.feedback_session:
                    self.start_stop_feedback(button_pressed=True)
        self.update_icons()
        return super(Feedback, self).eventFilter(obj, event)

    def update_icons(self):
        try:
            self.pause_player_button.setIcon(self.actual_icons[0])
            self.play_player_button.setIcon(self.actual_icons[1])
            self.record_player_button.setIcon(self.actual_icons[2])
            self.stop_player_button.setIcon(self.actual_icons[3])
        except RuntimeError:
            # all the C++ objects have been already deleted
            pass

    @Slot()
    def player_track_end(self):
        # check if there is an active feedback session
        if self.feedback_session:
            self.start_stop_feedback(stop_feedback=True)

        # disable the stop & pause buttons & enable the play button
        self.enable_disable_buttons(False, True)

        # restart the buttons colours
        self.actual_icons[0] = self.PAUSE_GRAY
        self.actual_icons[1] = self.PLAY_GRAY
        self.actual_icons[2] = self.RECORD_GRAY
        self.actual_icons[3] = self.STOP_GRAY
        self.update_icons()

    def generate_spectrogram(self):
        audio_file_name_mono = self.audio_file_name[:-4]+'_m.wav'

        # convert file to mono
        cmd = ['ffmpeg',
               '-y',
               '-i', self.audio_file_name,
               '-ac', '1',
               '-ab', '32k',
               '-ar', '11025',
               audio_file_name_mono]

        process = Popen(cmd)

        while True:
            if process.poll() is not None:
                break

        # read the wav file
        sampling_frequency, signal_data = wavfile.read(audio_file_name_mono)

        self.spectrogram.axes.cla()
        self.spectrogram.axes.axis('off')
        self.spectrogram.axes.plot(signal_data, color='#CCCCCC')
        self.spectrogram.draw()

        # delete the mono file
        os.remove(audio_file_name_mono)

    def start_stop_feedback(self, stop_feedback=False, button_pressed=False):
        if self.feedback_session or stop_feedback:
            # a feedback session is running
            # update database
            self.database.update_last_one(self.session_name_feedback_tab.currentText(),
                                          self.old_flow_level,
                                          self.last_position)
            self.old_flow_level = 0
            self.session_name_feedback_tab.setEnabled(True)
            return_dict = {
                'disable': False
            }
            self.enable_disable_recording_tab.emit_signal(return_dict)
            self.feedback_session = False
            self.play_player_button.setEnabled(True)
            if not stop_feedback or button_pressed:
                self.stop()
            else:
                # show the message box warning about the end of the session in 3 seconds
                _ = ui.TimerMessageBox(3,
                                       'Blue Haze - Stopping session',
                                       'Stopping automatically the feedback session in {} seconds',
                                       self).exec_()
        else:
            # let's start a feedback session
            self.last_position = 0
            self.actual_icons[2] = self.RECORD_RED
            self.update_icons()
            self.play()
            self.play_player_button.setEnabled(False)
            self.session_name_feedback_tab.setEnabled(False)
            return_dict = {
                'disable': True
            }
            self.enable_disable_recording_tab.emit_signal(return_dict)
            self.feedback_session = True

            # 1st entry
            self.database.clean_collection(self.session_name_feedback_tab.currentText())
            self.database.update_first_one(self.session_name_feedback_tab.currentText(), self.old_flow_level)