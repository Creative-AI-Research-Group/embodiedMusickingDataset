#
# Blue Haze
# Camera object
# 19 Oct 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

import cv2


class CameraManager:
    def __init__(self):
        self.__init__()


def list_cameras(self):
    """
    https://stackoverflow.com/questions/57577445/list-available-cameras-opencv-python?noredirect=1&lq=1
    https://www.iditect.com/how-to/53310665.html
    """
    index = 0
    cameras = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            print('Port {} is not available.'.format(index))
            break
        else:
            print('Found camera {}'.format(index))
            cameras.append(index)
        cap.release()
        index += 1
    return cameras
