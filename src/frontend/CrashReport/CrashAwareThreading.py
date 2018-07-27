# -*- coding: utf-8 -*-

# Providing the utilities that make python threads know what to do when unhandled exceptions occur.
# Typically opening the CrashReportApp and doing its stuff.
# This is a workaround against the python bug: http://bugs.python.org/issue1230540

# For the Main thread, just call installCrashReport()
# For other non-running-yet threads, just call installThreadExceptionHandler()

import threading, traceback, sys, os, asyncio
from CrashReport import CrashReport


class _PatchedThread(threading.Thread):
    def start(self):
        self._unpatched_run = self.run
        self.run = self.new_run
        super().start()

    def new_run(self):
        try:
            self._unpatched_run()
        except KeyboardInterrupt:
            pass
        except:
            sys.excepthook(*sys.exc_info())


def installThreadExceptionHandler():
    threading.Thread = _PatchedThread


def __installForReal():
    def __reportCrash(etype, value, tb):
        sys.__excepthook__(etype, value, tb)

        if issubclass(etype, KeyboardInterrupt):
            returnCode = os.EX_OK
        else:
            formatted = "".join(traceback.format_exception(etype, value, tb))
            CrashReport(formatted)
            returnCode = os.EX_SOFTWARE

        if threading.current_thread() == threading.main_thread():
            sys.exit(returnCode)  # Make sure MainThread exceptions also causes app termination.
        else:
            os._exit(returnCode)

    sys.excepthook = __reportCrash


def installCrashReport():
    thread = threading.current_thread()

    if not getattr(thread, "IsCrashAware", False):
        __installForReal()
        thread.IsCrashAware = True
    else:
        print("Already installed crash report on thread '{}'.".format(thread.name))


def _eventLoopHandler(_: "loop", context):
    exc = context.get("exception")
    tb = exc.__traceback__
    formatted = "".join(traceback.format_tb(tb))
    CrashReport(formatted)
    os._exit(os.EX_SOFTWARE)


def installEventLoopExceptionHandler():
    policy = asyncio.get_event_loop_policy()
    factory = policy._loop_factory

    class PatchedEventLoop(factory):
        def __init__(self, selector= None):
            super().__init__(selector)
            self.set_exception_handler(_eventLoopHandler)

    policy._loop_factory = PatchedEventLoop
