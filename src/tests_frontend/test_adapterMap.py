# -*- coding: utf-8 -*-

from collections import OrderedDict
from unittest import TestCase, mock
from models.AdapterMap import AdapterMap


class DummyKlassMap(OrderedDict):
    def __init__(self, namespace):
        super().__init__()
        self.__adapterMap = None
        self.namespace = namespace

    def setAdapterMap(self, adapterMap):
        self.__adapterMap = adapterMap


class AdapterMapTest(TestCase):
    def setUp(self):
        model = mock.Mock()
        self.am = AdapterMap(model = model)
        self.km1 = DummyKlassMap(namespace = "foo-1")
        self.km2 = DummyKlassMap(namespace = "bar-1")
        self.am.addKlassMap(klassMap = self.km1)
        self.am.addKlassMap(klassMap = self.km2)

    def test_addKlassMap_nonempty(self):
        self.km3 = DummyKlassMap(namespace = "nonempty-1")
        self.km3["1"] = 1
        self.km3["2"] = 2
        self.assertRaises(ValueError,
                          self.am.addKlassMap, self.km3)

    def test_addKlassMap(self):
        self.km1["1"] = 10
        self.km1["2"] = 2

        self.km2["1"] = 15
        self.km2["3"] = 3

        self.assertEqual(len(self.am), 4)
        self.assertListEqual(
            list(self.am.items()),
            [("foo-1|1", 10), ("foo-1|2", 2),
             ("bar-1|1", 15), ("bar-1|3", 3)]
        )

        self.assertListEqual(
            list(self.am.__iter__()),
            ["foo-1|1", "foo-1|2", "bar-1|1", "bar-1|3"],
        )

        self.assertEqual(self.am["foo-1|1"], 10)
        self.assertEqual(self.am["foo-1|2"], 2)
        self.assertEqual(self.am["bar-1|1"], 15)
        self.assertEqual(self.am["bar-1|3"], 3)

    def test_baseIndex(self):
        self.km1["1"] = 13
        self.km1["3"] = 32
        self.assertEqual(
            self.am.baseIndexForAdapter("foo-1"),
            0,
        )

        self.km2["6"] = 24
        self.km2["4"] = 53
        self.assertEqual(
            self.am.baseIndexForAdapter("bar-1"),
            2,
        )

        self.km1["2"] = 22
        self.assertEqual(
            self.am.baseIndexForAdapter("foo-1"),
            0,
        )
        self.assertEqual(
            self.am.baseIndexForAdapter("bar-1"),
            3,
        )

    def test_contains(self):
        self.km1["1"] = 11
        self.km1["2"] = 22
        self.km2["3"] = 33
        self.assertIn("foo-1|1", self.am)
        self.assertIn("foo-1|2", self.am)
        self.assertIn("bar-1|3", self.am)
        self.assertNotIn("bar-2|5", self.am)

    def test_at(self):
        self.km1["1"] = 11
        self.km1["2"] = 22
        self.km2["3"] = 33
        self.assertEqual(self.am.at(0), 11)
        self.assertEqual(self.am.at(1), 22)
        self.assertEqual(self.am.at(2), 33)

        # modifying value should change the position
        self.km1["1"] = 110
        self.assertEqual(self.am.at(0), 110)

        # add a new value to km1
        self.km1["88"] = 880
        self.assertEqual(self.am.at(2), 880)
        self.assertEqual(self.am.at(3), 33)

        # out-of-range
        self.assertRaises(
            IndexError,
            self.am.at, 4
        )
