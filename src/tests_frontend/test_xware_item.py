# -*- coding: utf-8 -*-

import unittest
from unittest import mock
from datetime import datetime
from urllib.parse import quote

from libxware.item import XwareTaskItem
from libxware.definitions import TaskClass as XwareTaskClass


def _mockLixianVipChannelFactory():
    result = {
        "type": 0,
    }
    return result


def _mockPayloadFactory(**kwargs):
    result = {
        "progress": 0,
        "remainTime": 0,
        "size": 1024,
        "vipChannel": _mockLixianVipChannelFactory(),
        "lixianChannel": _mockLixianVipChannelFactory(),
        "name": "Whatever",
        "path": "/what/ever",
        "url": "http://what/ever",
    }
    result.update(**kwargs)
    return result


class XwareItemTest(unittest.TestCase):
    def test_item_emit_completed(self):
        adapter = mock.Mock()
        adapter.namespace = "foo"
        taskModel = mock.Mock()

        # Initialize
        i = XwareTaskItem(adapter = adapter, taskModel = taskModel)
        i.update(_mockPayloadFactory(), xwareKlass = XwareTaskClass.RUNNING)
        self.assertRaises(AssertionError,
                          taskModel.taskCompleted.emit.assert_called_once_with, i)

        # Make it complete
        i.update(_mockPayloadFactory(completeTime = datetime.timestamp(datetime.now()),
                                     progress = 10000),
                 xwareKlass = XwareTaskClass.COMPLETED)
        taskModel.taskCompleted.emit.assert_called_once_with(i)

        # Don't emit long-ago completed
        i.update(_mockPayloadFactory(completeTime = 1, progress = 10000),
                 xwareKlass = XwareTaskClass.COMPLETED)
        taskModel.taskCompleted.emit.assert_called_once_with(i)

    def test_item_string_unquote(self):
        adapter = mock.Mock()
        adapter.namespace = "foo"
        taskModel = mock.Mock()

        # Initialize
        i = XwareTaskItem(adapter = adapter, taskModel = taskModel)
        i.update(_mockPayloadFactory(
            name = quote("/tmp/文件夹", safe = ""),
        ), xwareKlass = XwareTaskClass.RUNNING)
        self.assertEqual(i.name, "/tmp/文件夹")
