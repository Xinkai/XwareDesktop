# -*- coding: utf-8 -*-

from threading import Timer
import collections


GroupMembership = collections.namedtuple("GroupMembership", ["groupExists", "isIn", "isEffective"])


def debounce(wait, instant_first = True):
    # skip all calls that are invoked for a certain period of time, except for the last one.

    def debouncer(func):
        def debounced(*args, **kwargs):
            def call():
                return func(*args, **kwargs)

            if instant_first:
                if not hasattr(debounced, "initial_ran"):
                    setattr(debounced, "initial_ran", True)
                    return call()

            if hasattr(debounced, "t"):
                debounced.t.cancel()

            debounced.t = Timer(wait, call)
            debounced.t.daemon = True
            debounced.t.name = "debounced {}".format(func.__name__)
            debounced.t.start()
        return debounced
    return debouncer


def getGroupMembership(grpName):
    # return GroupMembership(bool, bool, bool)
    # first -> is the group exists
    # second -> is the user in the group
    # third -> is the group membership 'effective'
    import grp, getpass, os
    try:
        grpInfo = grp.getgrnam(grpName)
    except KeyError:
        return GroupMembership(False, False, False)

    gid, members = grpInfo[2], grpInfo[3]
    if getpass.getuser() not in members:
        return GroupMembership(True, False, False)

    effectiveGroups = os.getgroups()
    if gid not in effectiveGroups:
        return GroupMembership(True, True, False)

    return GroupMembership(True, True, True)
