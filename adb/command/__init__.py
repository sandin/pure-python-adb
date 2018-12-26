from adb.connection import DummyConnection


class Command:
    def create_connection(self, *args, **kwargs):
        return DummyConnection()
