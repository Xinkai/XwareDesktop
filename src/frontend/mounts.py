# -*- coding: utf-8 -*-

import constants
import os
import uuid

class MountsFaker(object):
    def __init__(self):
        self.mounts = []

        with open(constants.MOUNTS_FILE, "r") as mountsFile:
            lines = mountsFile.readlines()
            for line in lines:
                if line.replace("\t", "").replace(" ", "").replace("\n", "") == "":
                    continue # empty line

                lstripped = line.lstrip()
                if len(lstripped) > 0 and lstripped[0] == "#":
                    continue # comment

                parts = line.split()
                path = parts[1]

                self.mounts.append(path)

    def setMounts(self, mounts):
        self.mounts = mounts
        self.writeMounts()

    def convertToNativePath(self, path):
        assert path[:len(constants.ETM_MOUNTS_DIR)] == constants.ETM_MOUNTS_DIR

        path = path[len(constants.ETM_MOUNTS_DIR):]
        parts = path.split("/")
        drive = parts[0][:-1] # "C:" -> "C"
        return os.path.join(self.mounts[ord(drive)-ord("C")], *parts[1:])

    def writeMounts(self):
        buffer = []
        buffer.append(constants.MOUNTS_FILE_HEADER)

        def produceLine(path):
            # we only care about the first two columns
            return "UUID={uuid} {path} auto defaults,rw 0 0".format(uuid = str(uuid.uuid1()),
                                                                    path = path)

        for path in self.mounts:
            buffer.append(produceLine(path))

        buffer.append("")

        with open(constants.MOUNTS_FILE, "w") as mountFile:
            mountFile.writelines("\n".join(buffer))

    def getMountsMapping(self):
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

