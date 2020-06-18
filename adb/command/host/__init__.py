from adb.device import Device
from adb.command import Command
from adb.tracker import Tracker
from adb.parser import Parser
from adb import UnexpectedDataError
from adb.protocol import Protocol
import re

class Host(Command):
    CONNECT_RESULT_PATTERN = "(connected to|already connected)"

    def _execute_cmd(self, cmd):
        with self.create_connection() as conn:
            conn.send(cmd)
            result = conn.receive()
            return result

    def devices(self):
        cmd = "host:devices"
        result = self._execute_cmd(cmd)

        devices = []

        for line in result.split('\n'):
            if not line:
                break

            serial, _ = line.split()
            devices.append(Device(self, serial))

        return devices

    def devices_with_path(self):
        cmd = "host:devices-l"
        result = self._execute_cmd(cmd)

        devices = []
        for line in result.split('\n'):
            # 8e72a06b               device product:dipper model:MI_8 device:dipper
            # print(line)
            matched = re.match(r'(?P<serial>[\w\d.:]+)\s+(?P<path>.*model:(?P<model>[\S]+).*)', line)
            if not matched: continue
            groupdict = matched.groupdict()
            devices.append(Device(self, groupdict['serial'], model=groupdict['model'], path=groupdict['path']))

        return devices

    def version(self):
        with self.create_connection() as conn:
            conn.send("host:version")
            version = conn.receive()
            return int(version, 16)

    def kill(self):
        """
            Ask the ADB server to quit immediately. This is used when the
            ADB client detects that an obsolete server is running after an
            upgrade.
        """
        with self.create_connection() as conn:
            conn.send("host:kill")

        return True

    def track_devices(self, cb):
        conn = self.create_connection()
        parser = Parser(conn)
        conn.send("host:track-devices")
        Tracker(parser, cb)

    def connect(self, host, port):
        cmd = "host:connect:{host}:{port}".format(host=host, port=port)
        with self.create_connection() as conn:
            conn.send(cmd)
            return True, conn.receive()
            
    def disconnect(self, host, port):
        cmd = "host:disconnect:{host}:{port}".format(host=host, port=port)
        with self.create_connection() as conn:
            conn.send(cmd)
            return True, conn.receive()