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

    def update_first_one(self, collection, feedback):
        loop = asyncio.get_event_loop()
        _ = loop.run_until_complete(self.update_first_one_async(collection, feedback))

    async def update_first_one_async(self, collection, feedback):
        collection = self.db[collection]
        document = await collection.find_one_and_update(
            {'sync.backing_track_position': 0},
            {'$set': {
                'flow': feedback,
                'session.last_update': datetime.datetime.utcnow()
                }
            },
            new=True
        )
        return document

    def update_fields(self, collection, old_feedback, feedback, initial_position, actual_position):
        loop = asyncio.get_event_loop()
        _ = loop.run_until_complete(self.update_fields_async(collection,
                                                             old_feedback,
                                                             feedback,
                                                             initial_position,
                                                             actual_position))

    async def update_fields_async(self, collection, old_feedback, feedback, initial_position, actual_position):
        collection = self.db[collection]
        _ = await collection.update_many(
            {'sync.backing_track_position': {'$gt': initial_position, '$lt': actual_position-1}},
            {'$set': {'flow': old_feedback, 'session.last_update': datetime.datetime.utcnow()}}
        )
        _ = await collection.find_one_and_update(
            {'sync.backing_track_position': {'$gt': initial_position-1, '$lt': actual_position+1}},
            {'$set': {
                'flow': feedback,
                'session.last_update': datetime.datetime.utcnow()
                }
            },
            new=True
        )

    def update_last_one(self, collection, feedback, initial_position):
        loop = asyncio.get_event_loop()
        _ = loop.run_until_complete(self.update_last_one_async(collection, feedback, initial_position))

    async def update_last_one_async(self, collection, feedback, initial_position):
        collection = self.db[collection]
        _ = await collection.update_many(
            {'sync.backing_track_position': {'$gt': initial_position}},
            {'$set': {'flow': feedback, 'session.last_update': datetime.datetime.utcnow()}}
        )

    def close(self):
        self.client.close()
