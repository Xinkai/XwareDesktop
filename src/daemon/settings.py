# -*- coding: utf-8 -*-

XWARED_DEFAULTS_SETTINGS = {
    "xwared": {
        "startetm": True,
        "startetmwhen": 1,
    },
    "etm": {
        "shortlivedthreshold": 30,
        "samplenumberoflongevity": 3,
    },
}

from shared.config import SettingsAccessorBase
