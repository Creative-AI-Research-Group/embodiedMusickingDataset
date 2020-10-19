#
# Blue Haze
# 19 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtWidgets import (QApplication, QLabel, QPushButton,
                               QVBoxLayout, QWidget, QLineEdit,
                               QComboBox)
from PySide2.QtCore import Slot, Qt

import cv2
import sys


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setup_ui()

    def setup_ui(self):
        self.session_name = QLineEdit()
        self.camera = QComboBox()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.setWindowTitle('Blue Haze')
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec_())
