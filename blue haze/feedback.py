#
# Blue Haze
# 11 Jan 2021
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtWidgets import QGridLayout, QGroupBox, QLabel, QVBoxLayout, QComboBox, QHBoxLayout, QPushButton
from PySide2.QtGui import QIcon
from PySide2.QtCore import QSize
from database import *

import modules.config as cfg


class Feedback:
    def __init__(self):
        super().__init__()

        # stylesheet
        style_sheet = "background-color: none;"\
                      "border: none;"

        # list of sessions
        self.session_name_feedback_tab = QComboBox()
        self.session_name_feedback_tab.setDuplicatesEnabled(False)

        # player buttons
        self.pause_player_button = QPushButton()
        self.pause_player_button.setIcon(QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_pause.png'))
        self.pause_player_button.setIconSize(QSize(54, 54))
        self.pause_player_button.setStyleSheet(style_sheet)

        self.play_player_button = QPushButton()
        self.play_player_button.setIcon(QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_play.png'))
        self.play_player_button.setIconSize(QSize(68, 68))
        self.play_player_button.setStyleSheet(style_sheet)

        self.stop_player_button = QPushButton()
        self.stop_player_button.setIcon(QIcon(cfg.ASSETS_IMAGES_FOLDER + 'gray_stop.png'))
        self.stop_player_button.setIconSize(QSize(54, 54))
        self.stop_player_button.setStyleSheet(style_sheet)

        # start / stop area
        self.start_stop_button = QPushButton('Start')
        self.start_stop_label = QLabel()

        # database object
        self.database = Database()
        self.database.list_sessions()

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

        # get list of sessions
        self.get_list_sessions()

        return session_tab_layout

    def get_list_sessions(self):
        collections = self.database.list_sessions()
        for collection_name in collections:
            self.session_name_feedback_tab.addItem(collection_name)
