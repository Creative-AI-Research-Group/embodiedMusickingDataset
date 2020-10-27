from PySide2.QtWidgets import *
from PySide2.QtMultimedia import *
from PySide2.QtMultimediaWidgets import QCameraViewfinder
from PySide2.QtCore import Slot, Qt, QThread, QDir, QUrl

import sys


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.viewfinder = QCameraViewfinder()

        self.camera = QCamera(QCameraInfo.availableCameras()[1], self)
        self.camera_recorder = QMediaRecorder(self.camera)
        self.camera_recorder.stateChanged.connect(self.update_recorder_state)
        self.camera_recorder.statusChanged.connect(self.update_recorder_status)

        print(self.camera_recorder.supportedContainers())
        print(self.camera_recorder.supportedVideoCodecs())

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
        settings = self.camera_recorder.videoSettings()
        settings.setQuality(QMultimedia.VeryHighQuality)
        # settings.setResolution(640, 480)
        # settings.setFrameRate(24.0)
        settings.setCodec('video/x-h264')
        self.camera_recorder.setVideoSettings(settings)
        self.camera_recorder.setContainerFormat('video/quicktime')
        self.camera_recorder.setOutputLocation(QUrl.fromLocalFile('/home/sandbenders/teste.mov'))
        self.camera.setCaptureMode(QCamera.CaptureVideo)
        self.camera.start()

    def print_statuses(self):
        print(self.camera_recorder.state())
        print(self.camera_recorder.status())
        print(self.camera_recorder.error())
        print(self.camera_recorder.availability())

    def closeEvent(self, event):
        print('closing')
        self.camera_recorder.stop()
        event.accept()

    @Slot()
    def update_recorder_state(self):
        print('-- RECORDER STATE CHANGED')
        self.print_statuses()

    @Slot()
    def update_recorder_status(self):
        print('-- RECORDER STATUS CHANGED')
        self.print_statuses()
        if 'LoadedStatus' in str(self.camera_recorder.status()):
            print('L O A D E D')
            self.camera_recorder.record()

    @Slot()
    def update_availability_status(self):
        print('-- AVAILABILITY CHANGED!')
        self.print_statuses()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    widget = MainWindow()
    widget.setFixedSize(1350, 950)
    widget.show()

    sys.exit(app.exec_())