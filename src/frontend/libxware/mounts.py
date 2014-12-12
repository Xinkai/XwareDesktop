# -*- coding: utf-8 -*-

from collections import OrderedDict, namedtuple
import os

import constants
from utils.misc import trySymlink, tryMkdir, pathSplit


def _mountBootstrap(localPath):
    # local/path is the path that user sets
    # after bootstrapping, return the path to PROFILE/mnt/local\path

    # the filter(bool) part is to remove the "/" at the beginning
    backslashed = "\\".join(pathSplit(localPath))

    mntDir = os.path.join(constants.PROFILE_DIR, "mnt", backslashed)

    tddownloadDir = os.path.join(mntDir, "TDDOWNLOAD")
    thunderdbDir = os.path.join(mntDir, "ThunderDB")

    tryMkdir(thunderdbDir)
    trySymlink(localPath, tddownloadDir)

    return mntDir

MountsParseResult = namedtuple("MountsParseResult", ["localPath", "mntPath"])


def parseMountsFile(lines: "list of line") -> "list of (localPath, mntPath) pairs":
    result = []
    for line in lines:
        if line.replace("\t", "").replace(" ", "").replace("\n", "") == "":
            continue  # empty line

        lstripped = line.lstrip()
        if len(lstripped) > 0 and lstripped[0] == "#":
            continue  # comment

        parts = line.split()
        localPath, mntPath = parts[0], parts[1]
        result.append(MountsParseResult(localPath, mntPath))
    return result


class MountsFaker(object):
    # Terminologies:
    # local path: a path that the user sets
    # mnt path: the path which is mapped from a local path
    #           for example, PROFILE/mnt/mnt\unix

    def __init__(self, mountsFilePath: str):
        self._mounts = OrderedDict()
        self.__mountsFilePath = mountsFilePath

        with open(self.__mountsFilePath, "r", encoding = "UTF-8") as mountsFile:
            lines = mountsFile.readlines()

        parseResults = parseMountsFile(lines)
        for one in parseResults:
            self._mounts[one.mntPath] = one.localPath

    @property
    def mounts(self):
        # encapsulate self._mounts, which is an ordereddict of <mntPath:localPath>
        # only expose a list of <localPath>
        return list(self._mounts.values())

    @mounts.setter
    def mounts(self, paths):
        newMounts = OrderedDict()
        for localPath in paths:
            mntPath = _mountBootstrap(localPath)
            newMounts[mntPath] = localPath

        # write mount file
        buffer = list()
        buffer.append(constants.MOUNTS_FILE_HEADER)

        for mntPath, localPath in newMounts.items():
            # we only care about the first two columns
            buffer.append("{localPath} {mntPath} auto defaults,rw 0 0"
                          .format(localPath = localPath, mntPath = mntPath))

        buffer.append("")

        with open(self.__mountsFilePath, "w", encoding = "UTF-8") as mountFile:
            mountFile.writelines("\n".join(buffer))

        self._mounts = newMounts

    def convertToLocalPath(self, path):
        # takes a path like "/tmp/thunder/volumes/C:/TDDOWNLOAD/1.zip"
        # returns a local path "/home/user/Download/1.zip"

        tmp1 = path[:len(constants.ETM_MOUNTS_DIR)]
        tmp2 = constants.ETM_MOUNTS_DIR
        assert tmp1 == tmp2, (tmp1, tmp2)

        path = path[len(constants.ETM_MOUNTS_DIR):]  # remove "/tmp/thunder/volumes/" prefix
        parts = path.split("/")  # ["C:", "TDDOWNLOAD", "1.zip"]
        drive = parts[0][:-1]  # "C:" -> "C"

        localPath = os.path.join(
            self.mounts[ord(drive) - ord("C")],
            *parts[2:]  # discard "C:" and "TDDOWNLOAD"
        )
        resolvedLocalPath = os.path.realpath(localPath)

        return resolvedLocalPath

    def convertToMappedPath(self, localPath):
        # takes a path like "/home/user/Download"
        # returns a mapped path like "X:/TDDOWNLOAD/"
        if localPath[-1] != "/":
            localPath += "/"

        bestMatchCount = -1
        bestMatchDriveIndex = -1
        localParts = pathSplit(localPath)
        for i, path in enumerate(self.mounts):
            # i -> 0, 1, 2...
            # path -> "/home/user/Download"
            parts = pathSplit(path)
            for m, (local, against) in enumerate(zip(localParts, parts)):
                if local == against:
                    if m > bestMatchCount:
                        bestMatchCount = m
                        bestMatchDriveIndex = i
                else:
                    break

        path = self.mounts[bestMatchDriveIndex]  # not end with "/"

        if bestMatchDriveIndex >= 0:
            return "".join([
                self.driveIndexToLetter(bestMatchDriveIndex),  # "C:"
                "/TDDOWNLOAD",
                localPath[len(path):-1]                        # "may/be/sub/dir"
            ]) + "/"                                           # always end with a /
        else:
            return None

    def getMountsMapping(self):
        # checks when ETM really uses
        # returns a dict of {mntPath: drive}: {"$PROFILE/mnt/mnt\Downloads": "C:"}
        mapping = {}
        try:
            for drive in os.listdir(constants.ETM_MOUNTS_DIR_WITHOUT_CHMNS):
                # drive is like "C:", "D:"
                mntPath = os.path.realpath(constants.ETM_MOUNTS_DIR_WITHOUT_CHMNS + drive)
                try:
                    localPath = self._mounts[mntPath]
                except KeyError:
                    raise KeyError("触发问题#131。", drive, mntPath, self._mounts)
                mapping[localPath] = drive
        except FileNotFoundError:
            pass
        return mapping

    @staticmethod
    def driveIndexToLetter(index):
        # 0 -> "C:", 1 -> "D:", ...
        return chr(ord('C') + index) + ":"
