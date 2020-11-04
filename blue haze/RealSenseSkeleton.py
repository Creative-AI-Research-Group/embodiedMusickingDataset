#
# Blue Haze
# RealSense camera skeleton class
# 4 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from skeletontracker import SkeletonReader


class RealSenseSkeleton:
    def __init__(self):
        self.skeleton = SkeletonReader()

    def skeleton_read(self):
        return self.skeleton.read()

    def skeleton_terminate(self):
        self.skeleton.terminate()

