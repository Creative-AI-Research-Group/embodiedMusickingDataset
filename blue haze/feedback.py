#
# Blue Haze
# 11 Jan 2021
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtWidgets import QGridLayout, QGroupBox, QLabel, QVBoxLayout, QComboBox
from database import *

class Feedback:
    def __init__(self):
        super().__init__()

        # list of sessions
        self.session_name_feedback_tab = QComboBox()

        # database object
        self.database = Database()

    def ui_tab_feedback_tab_widget(self):
        # session field
        session_to_edit = QGridLayout()
        session_to_edit_group_box = QGroupBox()
        session_to_edit_layout = QGridLayout()
        session_to_edit_layout.setSpacing(8)

        # session name
        session_to_edit_name = QLabel('Session name: ')

        # fields layout
        session_to_edit_layout.addWidget(session_to_edit_name, 0, 1)
        session_to_edit_layout.addWidget(self.session_name_feedback_tab, 0, 2)
        session_to_edit_layout.setColumnStretch(3, 1)

        session_to_edit_group_box.setLayout(session_to_edit_layout)
        session_to_edit.addWidget(session_to_edit_group_box)

        # layout
        session_tab_layout = QVBoxLayout()
        session_tab_layout.addLayout(session_to_edit)

        return session_tab_layout

    def get_list_sessions(self):
        pass
