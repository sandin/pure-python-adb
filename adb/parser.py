from adb.protocol import Protocol
from adb import PrematureEOFError, FailError


class Parser:

    def __init__(self, conn):
        self.conn = conn

    def end(self):
        self.conn.close()

    def readAscii(self, bytes):
        return self.readBytes(bytes).decode("ascii")

    def readBytes(self, bytes):
        nr = 0
        ret = []
        while nr < bytes:
            buf = self.conn.read(bytes - nr)
            if not buf: raise PrematureEOFError("readBytes")
            nr += len(buf)
            ret.append(buf)
        return b''.join(ret)

    def readValue(self):
        value = self.readBytes(4)
        length = Protocol.decode_length(value)
        return self.readBytes(length)

    def readError(self):
        value = self.readValue()
        raise FailError(value)
