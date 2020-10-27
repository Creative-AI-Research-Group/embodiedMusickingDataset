from PySide2.QtWidgets import *
from PySide2.QtMultimedia import *
from PySide2.QtMultimediaWidgets import QCameraViewfinder
from PySide2.QtCore import Slot, Qt, QThread, QDir, QUrl

from subprocess import Popen

import sys


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.viewfinder = QCameraViewfinder()

        self.camera = QCamera(QCameraInfo.availableCameras()[1], self)

        self.process = None

        self.setup_ui()
        self.setup_camera()

    def setup_ui(self):
        layout = QVBoxLayout()
        view_finder_group_box = QGroupBox()
        view_finder_layout = QGridLayout()
        view_finder_layout.addWidget(self.viewfinder, 1, 1)
        view_finder_group_box.setLayout(view_finder_layout)
        layout.addWidget(view_finder_group_box)
        self.setLayout(layout)

    def setup_camera(self):
        self.camera.setViewfinder(self.viewfinder)
        self.camera.start()

        cmd = ['ffmpeg', '-f', 'dshow', '-i', 'video=HUE HD Camera', 'out.avi']
        self.process = Popen(cmd)

    def closeEvent(self, event):
        print('closing')
        self.process.terminate()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.setFixedSize(1350, 950)
    widget.show()

    sys.exit(app.exec_())