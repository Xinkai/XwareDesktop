# -*- coding: utf-8 -*-

from .model import Action


class Win32PowerActionManager(object):
    def __init__(self):
        self.actions = [Action.Null]

    def act(self, action):
        raise NotImplementedError("Cannot do {}".format(action))
