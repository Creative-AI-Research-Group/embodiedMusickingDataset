#
# Blue Haze
# Parse config file
# 16 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from configparser import ConfigParser

config_object = ConfigParser()
config_object.read('config.ini')

HARDWARE = config_object['HARDWARE'].getboolean('hardware')

UI_WIDTH = int(config_object['UI']['size_w'])
UI_HEIGHT = int(config_object['UI']['size_h'])

ASSETS_IMAGES_FOLDER = config_object['FOLDERS']['images']
ASSETS_BACKING_AUDIO_FOLDER = config_object['FOLDERS']['backing_audio']