#
# Blue Haze
# Database - mongoDB
# 5 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

import motor.motor_asyncio
import datetime
import asyncio
import traceback


class Database:
    def __init__(self,
                 session_id,
                 session_name,
                 audio_file,
                 mic_volume,
                 video_file,
                 backing_track_file):
        self.session_id = session_id
        self.session_name = session_name
        self.audio_file = audio_file
        self.mic_volume = mic_volume
        self.video_file = video_file
        self.backing_track_file = backing_track_file

        self.client = motor.motor_asyncio.AsyncIOMotorClient()
        self.db = self.client.blue_haze_database

    def insert(self,
               timestamp,
               delta_time,
               backing_track_position,
               bitalino_data,
               brainbit_data,
               skeleton_data):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.insert_document(timestamp=timestamp,
                                                     delta_time=delta_time,
                                                     backing_track_position=backing_track_position,
                                                     bitalino_data=bitalino_data,
                                                     brainbit_data=brainbit_data,
                                                     skeleton_data=skeleton_data))

    async def insert_document(self,
                              timestamp,
                              delta_time,
                              backing_track_position,
                              bitalino_data,
                              brainbit_data,
                              skeleton_data):
        post = {'session': {'id': self.session_id,
                            'name': self.session_name,
                            'date': datetime.datetime.utcnow(),
                            'last_update': None},
                'sync': {'timestamp': timestamp,
                         'delta': delta_time,
                         'backing_track_position': backing_track_position},
                'files': {'audio': {'file': self.audio_file,
                                    'mic_volume': self.mic_volume},
                          'video': self.video_file,
                          'backing_track': self.backing_track_file},
                'hardware': {'bitalino': bitalino_data,
                             'brainbit': brainbit_data,
                             'skeleton': skeleton_data},
                'flow': None}
        collection = self.db.get_collection(self.session_name)
        result = await collection.insert_one(post)

    def close(self):
        self.client.close()
