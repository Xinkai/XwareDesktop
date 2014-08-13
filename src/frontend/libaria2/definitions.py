# -*- coding: utf-8 -*-

import enum


@enum.unique
class Aria2TaskClass(enum.IntEnum):
    Active = 0
    Waiting = 1
    Stopped = 2


@enum.unique
class Aria2Method(enum.Enum):
    AddUri = "aria2.addUri"
    AddTorrent = "aria2.addTorrent"
    AddMetaLink = "aria2.addMetalink"
    Remove = "aria2.remove"
    ForceRemove = "aria2.forceRemove"
    Pause = "aria2.pause"
    PauseAll = "aria2.pauseAll"
    ForcePause = "aria2.forcePause"
    ForcePauseAll = "aria2.forcePauseAll"
    Unpause = "aria2.unpause"
    UnpauseAll = "aria2.unpauseAll"
    TellStatus = "aria2.tellStatus"
    GetUris = "aria2.GetUris"
    GetFiles = "aria2.GetFiles"
    GetPeers = "aria2.GetPeers"
    GetServers = "aria2.GetServers"
    TellActive = "aria2.tellActive"
    TellWaiting = "aria2.tellWaiting"
    TellStopped = "aria2.tellStopped"
    ChangePosition = "aria2.changePosition"
    ChangeUri = "aria2.changeUri"
    GetOption = "aria2.getOption"
    ChangeOption = "aria2.changeOption"
    GetGlobalOption = "aria2.getGlobalOption"
    ChangeGlobalOption = "aria2.changeGlobalOption"
    GetGlobalStat = "aria2.getGlobalStat"
    PurgeDownloadResult = "aria2.purgeDownloadResult"
    RemoveDownloadResult = "aria2.removeDownloadResult"
    GetVersion = "aria2.getVersion"
    GetSessionInfo = "aria2.getSessionInfo"
    Shutdown = "aria2.shutdown"
    ForceShutdown = "aria2.forceShutdown"
    SaveSession = "aria2.saveSession"
    MultiCall = "system.multicall"
