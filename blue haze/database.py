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
import json

import modules.utils as utls


class Database:
    def __init__(self,
                 session_id=None,
                 session_name=None,
                 mic_volume=None,
                 video_file=None,
                 backing_track_file=None):
        if session_id is not None:
            self.session_id = session_id
            self.session_name = session_name
            self.mic_volume = mic_volume
            self.video_file = video_file
            self.backing_track_file = backing_track_file

        self.client = motor.motor_asyncio.AsyncIOMotorClient()
        self.db = self.client.blue_haze_database

    def insert(self,
               delta_time,
               backing_track_position,
               chorus_id,
               bitalino_data,
               brainbit_data,
               skeleton_data):
        if self.session_id is None:
            utls.logger.error('Parameters not specified')
            return
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.insert_document(delta_time=delta_time,
                                                     backing_track_position=backing_track_position,
                                                     chorus_id=chorus_id,
                                                     bitalino_data=bitalino_data,
                                                     brainbit_data=brainbit_data,
                                                     skeleton_data=skeleton_data))

    async def insert_document(self,
                              delta_time,
                              backing_track_position,
                              chorus_id,
                              bitalino_data,
                              brainbit_data,
                              skeleton_data):
        post = {'session': {'id': self.session_id,
                            'name': self.session_name,
                            'date': datetime.datetime.utcnow(),
                            'last_update': None},
                'sync': {'delta': delta_time,
                         'backing_track_position': backing_track_position,
                         'chorus_id': chorus_id},
                'files': {'mic_volume': self.mic_volume,
                          'video': self.video_file,
                          'backing_track': self.backing_track_file},
                'hardware': {'bitalino': bitalino_data,
                             'brainbit': brainbit_data,
                             'skeleton': skeleton_data},
                'flow': None}
        collection = self.db.get_collection(self.session_name)
        _ = await collection.insert_one(post)

    def list_sessions(self):
        loop = asyncio.get_event_loop()
        collections = loop.run_until_complete(self.list_sessions_async())
        return collections

    async def list_sessions_async(self):
        return await self.db.list_collection_names()

    def get_audio_file_name(self, collection):
        loop = asyncio.get_event_loop()
        video_file_name = loop.run_until_complete(self.get_audio_file_name_async(collection))
        return video_file_name

    async def get_audio_file_name_async(self, collection):
        collection = self.db[collection]
        document = await collection.find_one({'_id': {'$exists': True}})
        return document['files']['video'][:-3]+'wav'

    def close(self):
        self.client.close()
