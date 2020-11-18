#
# Blue Haze
# Data Structures
# 16 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

from dataclasses import dataclass


@dataclass
class RecordSessionData:
    id: str = None
    date: str = None
    time_start: str = None
    name: str = None
    video_audio_path: str = None
    audio_file_name: str = None
    video_file_name: str = None
    audio_interface: str = None
    video_source: str = None
    mic_volume: float = 3
