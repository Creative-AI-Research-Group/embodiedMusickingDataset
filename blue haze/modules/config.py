#
# Blue Haze
# Parse config file
# 16 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

import json

from configparser import ConfigParser

config_object = ConfigParser()
config_object.read('config.ini')

DEBUG = config_object['DEBUG'].getboolean('debug')

HARDWARE = config_object['HARDWARE'].getboolean('hardware')

UI_WIDTH = config_object['UI'].getint('size_w')
UI_HEIGHT = config_object['UI'].getint('size_h')

ASSETS_IMAGES_FOLDER = config_object['FOLDERS']['images']
ASSETS_BACKING_AUDIO_FOLDER = config_object['FOLDERS']['backing_audio']

BITALINO_BAUDRATE = config_object['BITALINO'].getint('baudrate')
BITALINO_ACQ_CHANNELS = json.loads(config_object['BITALINO']['channels'])
BITALINO_MAC_ADDRESS = config_object['BITALINO']['mac_address']
