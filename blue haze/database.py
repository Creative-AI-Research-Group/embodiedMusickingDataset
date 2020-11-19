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
        db = self.client.blue_haze_database
        self.collection = db.blue_haze_posts

    def insert(self, timestamp, delta_time, bitalino_data, brainbit_data, skeleton_data):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.insert_document(timestamp, delta_time, bitalino_data, brainbit_data, skeleton_data))

    async def insert_document(self, timestamp, delta_time, bitalino_data, brainbit_data, skeleton_data):
        post = {'session_id': self.session_id,
                'session_name': self.session_name,
                'timestamp': timestamp,
                'delta_time': delta_time,
                'audio_file': self.audio_file,
                'mic_volume': self.mic_volume,
                'video_file': self.video_file,
                'backing_track_file': self.backing_track_file,
                'bitalino': bitalino_data,
                'brainbit': brainbit_data,
                'skeleton_data': skeleton_data,
                'flow_level': None,
                'date': datetime.datetime.utcnow(),
                'last_update': None}
        result = await self.collection.insert_one(post)

    def close(self):
        self.client.close()
