# -*- coding: utf-8 -*-

# This file make python threads know what to do when an unhandled exception occurs.
# Typically opens the CrashReportApp and do its stuff.
# This is a workaround against python bug: http://bugs.python.org/issue1230540

# For the Main thread, just call installCrashReport()
# For other non-running-yet threads, just call installThreadExceptionHandler()

import threading, traceback, sys, os
from CrashReport import CrashReport


class _PatchedThread(threading.Thread):
    def start(self):
        self._unpatched_run = self.run
        self.run = self.new_run
        super().start()

    def new_run(self):
        try:
            # super().run()
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

        formatted = "".join(traceback.format_exception(etype, value, tb))

        CrashReport(formatted)

        if threading.current_thread() == threading.main_thread():
            sys.exit(os.EX_SOFTWARE)  # Make sure MainThread exceptions also causes app termination.
        else:
            os._exit(os.EX_SOFTWARE)

    sys.excepthook = __reportCrash


def installCrashReport():
    thread = threading.current_thread()

    if not getattr(thread, "IsCrashAware", False):
        __installForReal()
        thread.IsCrashAware = True
    else:
        print("Already installed crash report on thread '{}'.".format(thread.name))
