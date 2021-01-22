#
# Blue Haze
# 11 Jan 2021
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtWidgets import *
from PySide2.QtGui import QIcon
from PySide2.QtCore import QSize, QEvent, Slot
from database import *
from playAudioTrack import PlayAudioTrack

import modules.config as cfg


class Feedback(QWidget):
    def __init__(self):
        super().__init__()

        # database object
        self.database = Database()

        # player object
        self.player = PlayAudioTrack(parent=self)

        # constants
        # icons
        self.PAUSE_GRAY = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_pause.png')
        self.PAUSE_RED = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'red_pause.png')
        self.PLAY_GRAY = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_play.png')
        self.PLAY_RED = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'red_play.png')
        self.STOP_GRAY = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_stop.png')
        self.STOP_RED = QIcon(cfg.ASSETS_IMAGES_FOLDER + 'red_stop.png')

        # player states
        self.PAUSED = self.player.State.PausedState
        self.PLAYING = self.player.State.PlayingState
        self.STOPPED = self.player.State.StoppedState

        '''
            [0] -> pause button
            [1] -> play button
            [2] -> stop button
        '''
        self.actual_icons = [self.PAUSE_GRAY,
                             self.PLAY_GRAY,
                             self.STOP_GRAY]

        # list of sessions
        self.session_name_feedback_tab = QComboBox()
        self.session_name_feedback_tab.setDuplicatesEnabled(False)

        # player buttons
        self.pause_player_button = QPushButton()
        self.play_player_button = QPushButton()
        self.stop_player_button = QPushButton()
        self.set_buttons()

        # start / stop area
        self.start_stop_button = QPushButton('Start')
        self.start_stop_label = QLabel()

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

        # session name
        session_to_edit_name = QLabel('Session: ')

        # fields layout
        session_to_edit_layout.addWidget(session_to_edit_name, 0, 1)
        session_to_edit_layout.addWidget(self.session_name_feedback_tab, 0, 2)
        session_to_edit_layout.setColumnStretch(3, 1)

        session_to_edit_group_box.setLayout(session_to_edit_layout)
        session_to_edit.addWidget(session_to_edit_group_box)

        # player
        player_group_box = QGroupBox()
        player_group_box.setMinimumHeight(800)
        player_layout = QGridLayout()
        player_layout.setSpacing(20)
        player_layout.addWidget(self.pause_player_button, 1, 1)
        player_layout.addWidget(self.play_player_button, 1, 2)
        player_layout.addWidget(self.stop_player_button, 1, 3)
        player_layout.setColumnStretch(0, 1)
        player_layout.setColumnStretch(4, 1)
        player_group_box.setLayout(player_layout)

        # start / stop button
        start_stop_button_group_box = QGroupBox()
        start_stop_button_layout = QHBoxLayout()
        self.start_stop_label.setPixmap(cfg.ASSETS_IMAGES_FOLDER + 'gray_start_stop.png')
        start_stop_button_layout.addStretch(1)
        start_stop_button_layout.addWidget(self.start_stop_label)
        start_stop_button_layout.addWidget(self.start_stop_button)
        start_stop_button_group_box.setLayout(start_stop_button_layout)

        # layout
        session_tab_layout = QVBoxLayout()
        session_tab_layout.addLayout(session_to_edit)
        session_tab_layout.addWidget(player_group_box)
        session_tab_layout.addWidget(start_stop_button_group_box)

        return session_tab_layout

    def get_list_sessions(self):
        collections = self.database.list_sessions()

        # clear the list to avoid duplicates
        self.session_name_feedback_tab.clear()

        for collection_name in collections:
            self.session_name_feedback_tab.addItem(collection_name)

    def play(self):
        audio_file_name = self.database.get_audio_file_name(self.session_name_feedback_tab.currentText())

        # enable the other buttons
        self.enable_disable_buttons(True)

        # check if the player is not paused
        if self.player.state() is not self.PAUSED:
            self.player.setup_media(audio_file_name)

        self.player.play()

    def stop(self):
        self.player.stop()

        # disable the stop & pause buttons & enable the play button
        self.enable_disable_buttons(False, True)

    def enable_disable_buttons(self, state_pause_stop=None, state_play=None):
        if state_pause_stop is not None:
            self.pause_player_button.setEnabled(state_pause_stop)
            self.stop_player_button.setEnabled(state_pause_stop)
        elif state_play is not None:
            self.play_player_button.setEnabled(state_play)

    def pause(self):
        # check if the player is already paused
        if self.player.state() is self.PAUSED:
            self.player.play()
        else:
            self.player.pause()

    def eventFilter(self, obj, event):
        # this is a bit messy and should be improved
        current_state = self.player.state()
        if event.type() is QEvent.HoverEnter:
            if obj is self.pause_player_button and current_state is not self.PAUSED:
                self.actual_icons[1] = self.PLAY_RED
                self.actual_icons[0] = self.PAUSE_RED
            elif obj is self.play_player_button and current_state is not self.PLAYING:
                self.actual_icons[1] = self.PLAY_RED
            elif obj is self.stop_player_button:
                self.actual_icons[2] = self.STOP_RED
        elif event.type() is QEvent.HoverLeave:
            if obj is self.pause_player_button and current_state is not self.PAUSED:
                self.actual_icons[0] = self.PAUSE_GRAY
            elif obj is self.play_player_button and current_state is not self.PLAYING:
                self.actual_icons[1] = self.PLAY_GRAY
            elif obj is self.stop_player_button:
                self.actual_icons[2] = self.STOP_GRAY
        elif event.type() is QEvent.MouseButtonPress:
            if obj is self.play_player_button:
                self.actual_icons[0] = self.PAUSE_GRAY
                self.actual_icons[1] = self.PLAY_RED
            elif obj is self.pause_player_button:
                if current_state is self.PAUSED:
                    self.actual_icons[0] = self.PAUSE_GRAY
                    self.actual_icons[1] = self.PLAY_RED
                else:
                    self.actual_icons[0] = self.PAUSE_RED
                    self.actual_icons[1] = self.PLAY_GRAY
            elif obj is self.stop_player_button:
                self.actual_icons[0] = self.PAUSE_GRAY
                self.actual_icons[1] = self.PLAY_GRAY
        self.update_icons()
        return super(Feedback, self).eventFilter(obj, event)

    def update_icons(self):
        self.pause_player_button.setIcon(self.actual_icons[0])
        self.play_player_button.setIcon(self.actual_icons[1])
        self.stop_player_button.setIcon(self.actual_icons[2])

    @Slot()
    def player_track_end(self):
        # reset the buttons
        self.enable_disable_buttons(False, True)
        self.play_player_button.setIcon(QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_play.png'))

