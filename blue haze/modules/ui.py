#
# Blue Haze
# Utils module
# 18 Dec 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtGui import QPalette, QColor
from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QMessageBox


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


# https://stackoverflow.com/questions/40932639/pyqt-messagebox-automatically-closing-after-few-seconds
class TimerMessageBox(QMessageBox):
    def __init__(self, timeout=3, title=None, text='Closing automatically in {} seconds', parent=None):
        super(TimerMessageBox, self).__init__(parent)
        self.text = text
        self.setWindowTitle(title)
        self.time_to_wait = timeout
        self.setText(self.text.format(timeout))
        self.setStandardButtons(QMessageBox.NoButton)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.change_content)
        self.timer.start()

    def change_content(self):
        self.setText(self.text.format(self.time_to_wait))
        if self.time_to_wait <= 0:
            self.close()
        self.time_to_wait -= 1

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()

