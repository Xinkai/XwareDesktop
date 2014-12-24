# -*- coding: utf-8 -*-

from unittest import TestCase, mock
from models.KlassMap import KlassMap
from models.TaskMapBase import TaskMapBase


class DummyTaskItem(object):
    def __init__(self, *, namespace, taskModel):
        self.value = None
        self.klass = None
        self.isDeletionPending = False
        self.__namespace = namespace
        self.__taskModel = taskModel

    def update(self, value, klass):
        self.value = value
        self.klass = klass


class KlassMapTest(TestCase):
    def setUp(self):
        adapter = mock.Mock()
        taskModel = mock.Mock()
        self.km = KlassMap(adapter = adapter, namespace = "foo-ins1", taskModel = taskModel)
        self.tm1 = TaskMapBase(klass = 0)
        self.tm1.__class__._Item = DummyTaskItem
        self.km.addTaskMap(self.tm1)
        self.tm2 = TaskMapBase(klass = 1)
        self.tm2.__class__._Item = DummyTaskItem
        self.km.addTaskMap(self.tm2)

        self.am = mock.Mock()
        self.km.setAdapterMap(self.am)

    def test_create_init(self):
        self.assertEqual(self.km.namespace, "foo-ins1")
        self.assertEqual(len(self.km), 0)
        self.assertRaises(NotImplementedError, self.km.__setitem__, "what", "ever")

        # namespace is set
        self.assertEqual(self.tm1.namespace, "foo-ins1")

    def test_create_same_klass(self):
        # try add it again, but with the same class
        tm1_1 = TaskMapBase(klass = 0)
        self.assertRaises(RuntimeError, self.km.addTaskMap, tm1_1)

    def test_task_add_update_delete(self):
        self.tm1.updateData({
            "1": "task1",
            "2": "task2",
        })
        self.assertEqual(len(self.km), 2)
        self.assertEqual(self.km["1"].value, "task1")
        self.assertEqual(self.km["1"].klass, 0)
        self.assertEqual(self.km["2"].value, "task2")
        self.assertEqual(self.km["2"].klass, 0)
        self.assertEqual(self.km["2"].isDeletionPending, False)

        # change item
        self.tm1.updateData({
            "1": "task1!",
            "2": "task2",
        })
        self.assertEqual(len(self.km), 2)
        self.assertEqual(self.km["1"].value, "task1!")
        self.assertEqual(self.km["2"].value, "task2")
        self.assertEqual(self.km["2"].isDeletionPending, False)

        # remove one item
        self.tm1.updateData({
            "1": "task1!",
        })
        self.assertEqual(len(self.km), 2)
        self.assertEqual(self.km["2"].isDeletionPending, True)

        # try to remove it again, shouldn't remove
        self.tm1.updateData({
            "1": "task1!",
        })
        self.assertEqual(len(self.km), 2)
        self.assertEqual(self.km["2"].isDeletionPending, True)

        # updateData with taskMap2
        self.tm2.updateData({})
        self.assertEqual(len(self.km), 1)
        self.assertRaises(KeyError, self.km.__getitem__, "2")

    def test_task_move(self):
        self.tm1.updateData({
            "1": "task1",
            "2": "task2",
        })

        self.tm2.updateData({
            "1": "task1??",
        })
        self.tm1.updateData({
            "2": "task2",
        })
        self.assertEqual(self.km["1"].isDeletionPending, True)

        # until tm1 deletes it, it shouldn't be in tm2
        self.assertEqual(len(self.tm1), 2)
        self.assertEqual(len(self.tm2), 0)

        # after tm2 updates again, it should be moved
        self.tm2.updateData({
            "1": "task1??",
        })
        self.assertEqual(len(self.tm1), 1)
        self.assertEqual(len(self.tm2), 1)
        self.assertEqual(self.tm2["1"].value, "task1??")
        self.assertEqual(self.tm1["2"].value, "task2")
        self.assertEqual(self.tm2["1"].isDeletionPending, False)

    def test_iter_index(self):
        self.tm1.updateData({
            "1": 10,
        })
        self.assertEqual(self.km.index("1"), 0)

        self.tm2.updateData({
            "4": 41,
        })
        self.assertEqual(self.km.index("4"), 1)

        self.tm2.updateData({
            "4": 41,
            "2": 25,
        })
        self.assertEqual(self.km.index("2"), 2)

        self.tm1.updateData({
            "1": 10,
            "3": 37,
        })
        self.assertEqual(self.km.index("3"), 1)

        for key in ["1", "2", "3", "4"]:
            self.assertTrue(key in self.km, key)
        self.assertListEqual(list(self.km.__iter__()), ['1', '3', '4', '2'])
