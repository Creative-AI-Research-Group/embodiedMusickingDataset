#
# Blue Haze
# Database - mongoDB
# 5 Nov 2020
#
# Fabrizio Poltronieri - fabrizio.poltronieri@dmu.ac.uk
# Craig Vear - cvear@dmu.ac.uk
#

# to perform async mongoDB operations
# see:
# https://api.mongodb.com/python/current/examples/gevent.html
# https://api.mongodb.com/python/current/faq.html#does-pymongo-support-asynchronous-frameworks-like-gevent-asyncio-tornado-or-twisted
import motor.motor_asyncio
import datetime
import asyncio


class Database:
    def __init__(self, session_id, session_name, audio_file, video_file):
        self.session_id = session_id
        self.session_name = session_name
        self.audio_file = audio_file
        self.video_file = video_file

        self.client = motor.motor_asyncio.AsyncIOMotorClient()
        db = self.client.blue_haze_database
        self.collection = db.blue_haze_posts

    def insert(self, timestamp, bitalino_data, brainbit_data, skeleton_data):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.insert_document(timestamp, bitalino_data, brainbit_data, skeleton_data))

    async def insert_document(self, timestamp, bitalino_data, brainbit_data, skeleton_data):
        post = {'session_id': self.session_id,
                'session_name': self.session_name,
                'timestamp': timestamp,
                'audio_file': self.audio_file,
                'video_file': self.video_file,
                'bitalino': bitalino_data,
                'brainbit': brainbit_data,
                'skeleton_data': skeleton_data,
                'flow_level': 0,
                'date': datetime.datetime.utcnow()}
        result = await self.collection.insert_one(post)

    def close(self):
        self.client.close()
