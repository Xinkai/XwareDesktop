# -*- coding: utf-8 -*-

from unittest import TestCase, mock
from Tasks.action import TaskCreationType, TaskCreation
from urllib.parse import urlparse


class TaskCreationTest(TestCase):
    def test_http(self):
        tc = TaskCreation(urlparse("http://www.example.com/down.mp3?id=3"))
        self.assertEqual(tc.kind, TaskCreationType.Normal)
        self.assertEqual(tc.url, "http://www.example.com/down.mp3?id=3")
        self.assertTrue(tc.isValid)

    def test_https(self):
        tc = TaskCreation(urlparse("https://www.example.net/down.zip"))
        self.assertEqual(tc.kind, TaskCreationType.Normal)
        self.assertEqual(tc.url, "https://www.example.net/down.zip")
        self.assertTrue(tc.isValid)

    def test_remoteTorrent(self):
        tc = TaskCreation(urlparse("http://www.abc.com/1.torrent?token=123"))
        self.assertEqual(tc.kind, TaskCreationType.RemoteTorrent)
        self.assertEqual(tc.url, "http://www.abc.com/1.torrent?token=123")
        self.assertTrue(tc.isValid)

    def test_localTorrent(self):
        tc = TaskCreation(urlparse("/home/user/1.torrent"))
        self.assertEqual(tc.kind, TaskCreationType.LocalTorrent)
        self.assertEqual(tc.url, "/home/user/1.torrent")
        self.assertTrue(tc.isValid)

    def test_metaLink(self):
        tc = TaskCreation(urlparse("https://download.net/5.metalink"))
        self.assertEqual(tc.kind, TaskCreationType.MetaLink)
        self.assertEqual(tc.url, "https://download.net/5.metalink")
        self.assertTrue(tc.isValid)

    def test_magnet(self):
        t = "magnet:?xt=urn:btih:ae5097941646d4fa76c9b83f0734d76787b9aaa0&dn=Suits.S03E14.720p.HDTV.x264-REMARKABLE%5Brartv%5D&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337"
        tc = TaskCreation(urlparse(t))
        self.assertEqual(tc.kind, TaskCreationType.Magnet)
        self.assertEqual(tc.url, t)
        self.assertTrue(tc.isValid)

    def test_emule(self):
        t = "ed2k://|file|Duck.Dynasty.S02E01.The.Grass.&.The.Furious.1080p.WEB-DL.AAC2.0.H.264-BTN.mkv|830442056|6E6F074D8FDAECDE8F4E2188439A107C|h=5X7ZMLTEVWW5PV7NVBHGA5W7BAVNC4OX|/"
        tc = TaskCreation(urlparse(t))
        self.assertEqual(tc.kind, TaskCreationType.Emule)
        self.assertEqual(tc.url, t)
        self.assertTrue(tc.isValid)

    def test_empty(self):
        tc = TaskCreation(None)
        self.assertEqual(tc.kind, TaskCreationType.Empty)
        self.assertEqual(tc.url, None)
        self.assertFalse(tc.isValid)

    def test_invalid_scheme(self):
        tc = TaskCreation(urlparse("what://ever/1.zip"))
        self.assertEqual(tc.kind, None)
        self.assertEqual(tc.url, "what://ever/1.zip")
        self.assertFalse(tc.isValid)

    def test_invalid_url(self):
        tc = TaskCreation(urlparse("http://domain."))
        self.assertEqual(tc.kind, TaskCreationType.Normal)
        self.assertEqual(tc.url, "http://domain.")
        self.assertFalse(tc.isValid)
