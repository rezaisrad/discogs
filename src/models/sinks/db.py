class BaseDataStore:
    def connect(self):
        raise NotImplementedError("Connect method must be implemented by subclass.")

    def insert(self, data):
        raise NotImplementedError("Insert method must be implemented by subclass.")
