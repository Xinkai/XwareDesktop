# -*- coding: utf-8 -*-

from pathlib import Path


def profileBootstrap(targetDir):
    profilePath = Path(targetDir)

    # Etm Cfg
    try:
        (profilePath / "cfg").mkdir(parents = True)
        (profilePath / "etc").mkdir(parents = True)
        (profilePath / "mntlinks").mkdir(parents = True)
        (profilePath / "tmp" / "thunder").mkdir(parents = True)
    except FileExistsError:
        pass

    for fileName in ("download.cfg", "cid_store.dat", "dht.cfg", "thunder_mounts.cfg", "etm.cfg",
                     "kad.cfg"):
        (profilePath / "cfg" / fileName).touch()

    for fileName in ("frontend.ini", "mounts", "xwared.ini"):
        (profilePath / "etc" / fileName).touch()
