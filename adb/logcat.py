from threading import Thread
from adb import PrematureEOFError
import logging
from functools import wraps
from logcat_parser import LogcatStreamParser, MessageParser

def cb_wrap(cb):
    @wraps(cb)
    def wrap(*largs, **kwargs):
        try:
            return cb(*largs, **kwargs)
        except:
            logging.exception("(in tracker callback)")
    return wrap

class LogcatParser:
    
    def __init__(self, conn):
        self.conn = conn
    
    def readLine(self):
        return self.conn.read(128)

class MyLogcatStreamParser(LogcatStreamParser):

    def __init__(self, conn, lah=b''):
        self._look_ahead = lah
        super().__init__(conn)

    def _read_raw(self, size):
        return self._stream.read(size)

    def _read_one(self):
        if self._look_ahead:
            if self._look_ahead != b'\r':
                ret = self._look_ahead
                self._look_ahead = b''
                return ret
            else:
                cur = self._look_ahead
                self._look_ahead = b''
        else:
            cur = self._stream.read(1)
        if cur != b'\r':
            return cur
        else:
            cur2 = self._stream.read(1)
            if cur2 == b'\n':
                return b'\n'
            else:
                self._look_ahead = cur2
                return cur

    def read(self, size, timeout=None):
        h = self._look_ahead
        ret = b''.join([self._read_one() for i in range(size)])
        return ret


class MyMessageParser(MessageParser):

    def __init__(self, parser):
        super().__init__(parser)
        self._data = dict(parser.items())
        self._data.update({
            'priority': self._priority,
            'tag': self._tag,
            'message': self._message,
        })


class FpWrapper:

    def __init__(self, fp):
        self.fp = fp
        self._buf = b''
        self._off = 0
        self._eof = False

    def _read_chunk(self):
        buf = self.fp.read(4096)
        if not buf:
            self._eof = True
            return
        if self._off:
            self._buf = self._buf[self._off:]
            self._off = 0
        self._buf += buf

    def read(self, bytes):
        while len(self._buf) < self._off + bytes and not self._eof:
            self._read_chunk()
        ret = self._buf[self._off: self._off + bytes]
        self._off += len(ret)
        return ret

class Logcat:
  
    def __init__(self, conn, cb):
        self.cb = cb_wrap(cb)
        self.conn = conn
        self.fp = FpWrapper(conn)
        thread = Thread(target=self._readdevices_loop, name="Logcat")
        thread.setDaemon(True)
        thread.start()
    
    def _readdevices_loop(self):
        try:
            while 1:
                _parser = MyLogcatStreamParser(self.fp)
                message = MyMessageParser(_parser[0])
                if not self.cb({"what": "log", "msg": message._data}):
                    break
        except PrematureEOFError:
            pass
        finally:
            self.cb({"what": "eof"})
            self.conn.close()