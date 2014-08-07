#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import asyncio
import json
from shared import XwaredSocketError


class XwaredClient(asyncio.Protocol):
    def __init__(self):
        super().__init__()
        self._data = b''

    def data_received(self, data):
        self._data += data

    def eof_received(self):
        data = json.loads(self._data.decode("utf-8"))
        self.donecb(data)

    @staticmethod
    def donecb(data):
        pass


@asyncio.coroutine
def callXwared(adapter: "XwareAdapter", method: "str", arguments: "jsonfiable"):
    loop = asyncio.get_event_loop()

    socketPath = adapter.xwaredSocket
    cb = getattr(adapter, "_donecb_daemon_" + method, None)

    try:
        transport, protocol = yield from loop.create_unix_connection(XwaredClient, path = socketPath)
        if cb:
            protocol.donecb = cb
        payload = {
            "method": method,
            "arguments": arguments,
        }
        payloadBytes = json.dumps(payload).encode("utf-8")
        transport.write(payloadBytes)
        transport.write_eof()
    except ConnectionRefusedError:
        if cb:
            cb({
                "error": XwaredSocketError.CLIENT_CONNECTION_REFUSED
            })
    except FileNotFoundError:
        if cb:
            cb({
                "error": XwaredSocketError.CLIENT_SOCKET_NOT_FOUND
            })
    except:
        if cb:
            cb({
                "error": XwaredSocketError.CLIENT_UNKNOWN
            })
