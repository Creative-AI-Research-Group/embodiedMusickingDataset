#
# Blue Haze
# Utils module
# 16 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

import logging
import modules.config as cfg

logger = logging.getLogger('blue_haze')

if cfg.DEBUG:
    logging.basicConfig(level=logging.DEBUG)

logging.basicConfig(format='(%asctime)s - %(message)s')
