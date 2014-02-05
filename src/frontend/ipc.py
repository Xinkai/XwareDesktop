# -*- coding: utf-8 -*-

import socket
import sys

sd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
sd.connect("/tmp/xware_socket")
if len(sys.argv) >= 2:
    sd.sendall(b"ETM_START\0")
else:
    sd.sendall(b"ETM_STOP\0")