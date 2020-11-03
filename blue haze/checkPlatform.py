#
# Blue Haze
# Check platform
# 30 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

import platform


def check_platform():
    # Linux: Linux
    # Mac: Darwin
    # Windows: Windows
    return platform.system()
