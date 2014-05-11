# -*- coding: utf-8 -*-

from collections import OrderedDict
import os
import uuid
import re
import subprocess

import constants


class MountsFaker(object):
    _mounts = None

    def __init__(self):
        self._mounts = OrderedDict()

        with open(constants.MOUNTS_FILE, "r", encoding = "UTF-8") as mountsFile:
            lines = mountsFile.readlines()
            for line in lines:
                if line.replace("\t", "").replace(" ", "").replace("\n", "") == "":
                    continue  # empty line

                lstripped = line.lstrip()
                if len(lstripped) > 0 and lstripped[0] == "#":
                    continue  # comment

                parts = line.split()
                path, uuid_ = parts[1], parts[0][len("UUID="):]

                self._mounts[path] = uuid_

    @property
    def mounts(self):
        # encapsulate self._mounts, which is an ordereddict of <path:uuid>
        # only expose a list of <path>
        return list(self._mounts.keys())

    @mounts.setter
    def mounts(self, paths):
        new_Mounts = OrderedDict()
        for path in paths:
            new_Mounts[path] = self._mounts.get(path, str(uuid.uuid1()))

        self._mounts = new_Mounts
        self.writeMounts()

    def convertToNativePath(self, path):
        assert path[:len(constants.ETM_MOUNTS_DIR)] == constants.ETM_MOUNTS_DIR

        path = path[len(constants.ETM_MOUNTS_DIR):]
        parts = path.split("/")
        drive = parts[0][:-1]  # "C:" -> "C"

        nativePath = os.path.join(self.mounts[ord(drive) - ord("C")], *parts[1:])
        resolvedPath = os.path.realpath(nativePath)
        return resolvedPath

    def writeMounts(self):
        buffer = list()
        buffer.append(constants.MOUNTS_FILE_HEADER)

        for path, uuid_ in self._mounts.items():
            # we only care about the first two columns
            buffer.append("UUID={uuid} {path} auto defaults,rw 0 0".format(uuid = uuid_,
                                                                           path = path))

        buffer.append("")

        with open(constants.MOUNTS_FILE, "w", encoding = "UTF-8") as mountFile:
            mountFile.writelines("\n".join(buffer))

    @staticmethod
    def getMountsMapping():
        # checks when ETM really uses
        mapping = {}
        try:
            for drive in os.listdir(constants.ETM_MOUNTS_DIR):
                # drive is like "C:", "D:"
                realpath = os.path.realpath(constants.ETM_MOUNTS_DIR + drive)
                mapping[realpath] = drive
        except FileNotFoundError:
            pass
        return mapping

    @staticmethod
    def permissionCheck():
        ansiEscape = re.compile(r'\x1b[^m]*m')

        with subprocess.Popen([constants.PERMISSIONCHECK],
                              stdout = subprocess.PIPE,
                              stderr = subprocess.PIPE) as proc:
            output = proc.stdout.read().decode("utf-8")
            output = ansiEscape.sub('', output)
            lines = output.split("\n")

        prevLine = None
        currMount = None
        result = {}
        for line in lines:
            if len(line.strip()) == 0:
                continue

            if all(map(lambda c: c == '=', line)):
                if currMount:
                    result[currMount] = result[currMount][:-1]

                result[prevLine] = []
                currMount = prevLine
                continue

            if currMount:
                if line != "正常。":
                    result[currMount].append(line)

            prevLine = line

        return result