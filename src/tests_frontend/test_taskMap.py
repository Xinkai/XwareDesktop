# -*- coding: utf-8 -*-

from unittest import TestCase, mock
from models.TaskMapBase import TaskMapBase

from .test_klassMap import DummyTaskItem


class TaskMapTest(TestCase):
    def setUp(self):
        self.tm = TaskMapBase(klass = 0)
        self.tm.__class__._Item = DummyTaskItem

    def test_ordereddict(self):
        self.tm[1] = 1
        self.tm[3] = 2
        self.tm[2] = 3
        self.tm[4] = 4
        self.assertEqual(list(self.tm.__iter__()),
                         [1, 3, 2, 4])

        self.assertEqual(self.tm[1], 1)
        self.assertEqual(self.tm[3], 2)
        self.assertEqual(self.tm[2], 3)
        self.assertEqual(self.tm[4], 4)

        self.assertRaises(KeyError, self.tm.__getitem__, "error")

        # __contains__
        for key in [1, 2, 3, 4]:
            self.assertTrue(key in self.tm)
        for key in [0, -1, 5]:
            self.assertTrue(key not in self.tm)

    def test_updateData_insert_modify(self):
        klassMap = mock.Mock()
        taskModel = mock.Mock()
        klassMap.beforeInsert = lambda *args: True
        self.tm.setKlassMap(klassMap)
        self.tm.setTaskModel(taskModel)
        self.tm.namespace = "foo-1"

        self.tm.updateData({
            2: 1,
        })
        self.tm.updateData({
            1: 11,
            2: 13,
        })

        self.assertEqual(list(self.tm.__iter__()),
                         [2, 1])
        self.assertTrue(1 in self.tm)
        self.assertTrue(2 in self.tm)

        self.assertEqual(self.tm[1].value, 11)
        self.assertEqual(self.tm[2].value, 13)

    def test_keys(self):
        klassMap = mock.Mock()
        taskModel = mock.Mock()
        klassMap.beforeInsert = lambda *args: True
        self.tm.setKlassMap(klassMap)
        self.tm.setTaskModel(taskModel)
        self.tm.namespace = "foo-1"

        self.tm.updateData({
            2: 1,
        })
        self.tm.updateData({
            1: 11,
            2: 13,
        })

        self.assertListEqual(list(self.tm.keys()), [2, 1])
