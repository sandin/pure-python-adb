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
    
    def read(self, size, timeout=None):
        return self._stream.read(size)

class MyMessageParser(MessageParser):
    
    def __init__(self, parser):
        super().__init__(parser)
        self._data = dict(parser.items())
        self._data.update({
            'priority': self._priority,
            'tag': self._tag,
            'message': self._message,
        })

class Logcat:
  
    def __init__(self, conn, cb):
        self.cb = cb_wrap(cb)
        self.conn = conn
        thread = Thread(target=self._readdevices_loop, name="Logcat")
        thread.setDaemon(True)
        thread.start()
    
    def _readdevices_loop(self):
        try:
            while 1:
                _parser = MyLogcatStreamParser(self.conn)
                message = MyMessageParser(_parser[0])
                if not self.cb({"what": "log", "msg": message._data}):
                    break
        except PrematureEOFError:
            pass
        finally:
            self.cb({"what": "eof"})