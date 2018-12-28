from threading import Thread
from adb import PrematureEOFError

class Tracker:

    def __init__(self, parser, cb):
        self.parser = parser
        self.cb = cb
        self.devices = set()
        thread = Thread(target=self._readdevices_loop, name="Tracker")
        thread.setDaemon(True)
        thread.start()
    
    def _update(self, devices):
        current = set([d[0] for d in devices])
        gone = self.devices - current
        new = current - self.devices
        for d in gone:
            self.cb("device gone: %s" % d)
        for d in new:
            self.cb("device online: %s" % d)
        self.devices = current

    def _readdevices_loop(self):
        try:
            while 1:
                value = self.parser.readValue()
                self._update(
                    filter(lambda p: len(p) == 2 and p[1] == u'device',
                        map(lambda s:s.split(u'\t', 1), value.decode('utf8').split(u'\n')
                        )
                    )
                )
        except PrematureEOFError:
            pass
        finally:
            self.cb("connection lost")