#
# Blue Haze
# Utils module
# 18 Dec 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from PySide2.QtGui import QPalette, QColor
from PySide2.QtCore import Qt


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
