import redis
import json
from .db import BaseDataStore

class RedisDataStore(BaseDataStore):
    def __init__(self, host="localhost", port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.connection = None

    def connect(self):
        self.connection = redis.Redis(host=self.host, port=self.port, db=self.db)

    def insert(self, records):
        if not self.connection:
            self.connect()
        with self.connection.pipeline() as pipe:
            for record in records:
                key = f"release:{record['id']}"
                value = json.dumps(record)
                pipe.set(key, value)
            pipe.execute()
