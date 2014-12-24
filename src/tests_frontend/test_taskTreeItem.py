# -*- coding: utf-8 -*-

from unittest import TestCase, mock

from PyQt5.Qt import Qt
from models.TaskTreeItem import TaskTreeItem


class TaskTreeItemTest(TestCase):
    def test_create_root(self):
        tti = TaskTreeItem()

        self.assertTrue(tti.isRoot())
        self.assertEqual(tti.ancestryTree, "ROOT")
        self.assertEqual(tti.name, "UNKNOWN")
        self.assertEqual(tti.size, 0)
        self.assertEqual(tti.index, -1)
        self.assertIsNone(tti.parent)
        self.assertEqual(tti.selected, Qt.Unchecked)

        self.assertFalse(tti.children)
        self.assertEqual(tti.childrenCount(), 0)

        self.assertFalse(tti.siblings)
        with self.assertRaises(ValueError):
            tti.siblingNumber()

    def test_set_name(self):
        tti = TaskTreeItem()
        tti.name = "Root"
        self.assertEqual(tti.name, "Root")

    def test_add_task(self):
        root = TaskTreeItem()
        root.addSubTask(name = "Folder", size = 1035, index = 555, selected = False)

        self.assertListEqual(list(root.children.keys()), ["Folder"])

        folder = root / "Folder"
        self.assertEqual(folder.name, "Folder")
        self.assertEqual(folder.size, 1035)
        self.assertEqual(folder.index, 555)
        self.assertEqual(folder.selected, Qt.Unchecked)

    def test_add_task_task(self):
        root = TaskTreeItem()
        root.addSubTask(name = "Folder", size = 1035, index = 555, selected = False)
        root.addSubTask(name = "Folder/document", size = 1354, index = 334, selected = False)

        self.assertListEqual(list(root.children.keys()), ["Folder"])
        # folder size is the total size of children
        folder = root / "Folder"
        self.assertEqual(folder.size, 1354)

        doc = root / "Folder" / "document"
        self.assertListEqual(list(doc.children.keys()), [])
        self.assertEqual(doc.name, "document")
        self.assertEqual(doc.size, 1354)
        self.assertEqual(doc.index, 334)
        self.assertEqual(doc.selected, Qt.Unchecked)

    def test_selection_size(self):
        root = TaskTreeItem()
        root.addSubTask(name = "Folder", size = 0, index = 1, selected = False)
        root.addSubTask(name = "Dir/video.mp4", size = 5000, index = 2, selected = False)
        root.addSubTask(name = "Folder/document", size = 3000, index = 3, selected = True)

        self.assertEqual(root.selected, Qt.PartiallyChecked)
        self.assertEqual(root.size, 8000)

        dir_ = root / "Dir"
        self.assertEqual(dir_.selected, Qt.Unchecked)
        self.assertEqual(dir_.size, 5000)

        video = root / "Dir" / "video.mp4"
        self.assertEqual(video.selected, Qt.Unchecked)
        self.assertEqual(video.size, 5000)

        folder = root / "Folder"
        self.assertEqual(folder.selected, Qt.Checked)
        self.assertEqual(folder.size, 3000)

        doc = root / "Folder" / "document"
        self.assertEqual(doc.selected, Qt.Checked)
        self.assertEqual(doc.size, 3000)
