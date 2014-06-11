# -*- coding: utf-8 -*-

try:
    from pathlib import Path
except ImportError:
    from shared.backports.pathlib import Path


def profileBootstrap(targetDir):
    profilePath = Path(targetDir)

    # Etm Cfg
    try:
        (profilePath / "cfg").mkdir(parents = True)
        (profilePath / "etc").mkdir(parents = True)
        (profilePath / "mnt").mkdir(parents = True)
        (profilePath / "tmp" / "thunder").mkdir(parents = True)
    except FileExistsError:
        pass

    for fileName in ("download.cfg", "cid_store.dat", "dht.cfg", "thunder_mounts.cfg", "etm.cfg",
                     "kad.cfg"):
        (profilePath / "cfg" / fileName).touch()

    for fileName in ("frontend.ini", "mounts", "xwared.ini"):
        (profilePath / "etc" / fileName).touch()
