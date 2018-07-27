# -*- coding: utf-8 -*-

import tempfile
import unittest

from shared.config import SettingsAccessorBase


class TestSettings(unittest.TestCase):
    def test_settings(self):
        d = {
            "foo": {
                "fooint": 1,
                "foofloat": 1.1,
                "foostr": "foo!",
            },
            "bar": {
                "bartrue": True,
                "barnone": None,
                "barfalse": False,
            },
        }
        with tempfile.NamedTemporaryFile() as f:
            text = """
[foo2]
nihao = hello
zaijian = 88

[bar]
bartrue = False
"""
            f.write(text.encode("UTF-8"))
            f.flush()
            s = SettingsAccessorBase(configFilePath = f.name, defaults = d)

            self.assertEqual(s.getint("foo", "fooint"), 1)
            self.assertEqual(s.getfloat("foo", "foofloat"), 1.1)
            self.assertEqual(s.get("foo", "foostr"), "foo!")
            self.assertTrue(s.has("foo", "foostr"))
            self.assertFalse(s.has("foo", "notthere"))

            self.assertEqual(s.getbool("bar", "bartrue"), False)
            self.assertEqual(s.get("bar", "barnone"), None)
            self.assertEqual(s.getbool("bar", "barfalse"), False)

            # proxy
            foo = s["foo"]
            self.assertEqual(foo.getint("fooint"), 1)
            self.assertEqual(foo.getfloat("foofloat"), 1.1)
            self.assertEqual(foo.get("foostr"), "foo!")
            self.assertTrue(foo.has("foostr"))
            self.assertFalse(foo.has("notthere"))

            bar = s["bar"]
            self.assertEqual(bar.getbool("bartrue"), False)
            self.assertEqual(bar.get("barnone"), None)
            self.assertEqual(bar.getbool("barfalse"), False)

            names = []
            for secName, sec in s.itr_sections_with_prefix("foo"):
                names.append(secName)
            self.assertSetEqual(set(names), {"foo", "foo2"})

            foo2 = s["foo2"]
            self.assertEqual(foo2.get("nihao"), "hello")

            # set
            foo.setfloat("pi", 3.1415)
            s.setint("bar", "bartrue", 5)
            s.setbool("foo2", "zaijian", True)

            # access the non-existent
            self.assertRaises(KeyError, s.__getitem__, "walala")
            self.assertRaises(KeyError, foo.__getitem__, "walala")
            self.assertRaises(KeyError, foo2.__getitem__, "walala")

            s.save()

            f.seek(0)
            self.assertEqual(
                f.read(),
                b"""[foo2]
nihao = hello
zaijian = 1

[bar]
bartrue = 5

[foo]
pi = 3.1415

""")
