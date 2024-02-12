import redis
from sinks import BaseDataStore

class RedisDataStore(BaseDataStore):
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.connection = None

    def connect(self):
        self.connection = redis.Redis(host=self.host, port=self.port, db=self.db)
    
    def insert(self, key, value):
        if not self.connection:
            self.connect()
        self.connection.set(key, value)
    
    def query(self, key):
        if not self.connection:
            self.connect()
        return self.connection.get(key)
