# -*- coding: utf-8 -*-

import unittest
from Tasks import mimeparser

testCases = """
迅雷专链
thunder://QUFodHRwOi8vaW0uYmFpZHUuY29tL2luc3RhbGwvQmFpZHVIaS5leGVaWg==

一般的文件
http://www.163.com/robots.zip

包含dash
ftp://dashingdash.com/1-2.txt

包含用户名
http://username@www.263.com/robots.cab

包含用户名、密码及复合扩展名
http://user-name+1.23_ok:pass@www.w3c.com/spec.tar.gz
http://user:pa+ss-wo_rd1.23@www.w3c.com/1.tar.gz

用户名、密码：以下几种情况不应匹配
ftp://用户@253.com/5555.txt
ftp://user:中文密码@253.com/5555.txt
ftp://user:%20%65@253.com/5555.txt
ftp://user: pass @253.com/5555.txt

包含用户名、密码、端口
http://un:pass@www.444.com:1353/robots.txt

一个参数
http://www.555.com/player.wmv?ab=3
http://www.555.com/player.exe?ab=3

多个参数
http://666.com/player.mp3?ab=3&cd=opq
http://666.com/player.exe?ab=3&cd=opq

ip地址、中文路径名
http://71.35.264.35/测试.7zip
http://71.35.264.35/测试.cab

特殊符号 u3010, u3011
https://1.2.3.4/【1】.zip

https、下划线、逗号、横线，网址编码
https://localhost:8000/test_page.zip?ab=3-5,5-6&cd=%20&callback=foo_bar

网址noise：结尾
http://106.20.35.62/1.zip1

网址noise：多重扩展名
http://127.0.0.1/bar.zip.php
http://127.0.0.1/bar.php.zip

网址noise：query部分带有
http://site.com/upload.php?to=/2014/08/08/test.zip

大小写
HtTP://test.com/foo.zIP

url with hash
http://www.test.com/1.exe#download

url frags
http://www.test.com/1.exe?op=DOWNLOAD#foo

正常文本
锄禾日当午 汗滴禾下土 谁知盘中餐 粒粒皆辛苦

ed2k
ed2k://|file|The_Two_Towers-The_Purist_Edit-Trailer.avi|14997504|965c013e991ee246d63d45ea71954c4d|/

ed2k with additional data
ed2k://|file|The_Two_Towers-The_Purist_Edit-Trailer.avi|14997504|965c013e991ee246d63d45ea71954c4d|/|sources,202.89.123.6:4662|/

another ed2k
ed2k://|file|%E6%B5%81%E8%A8%80%E7%BB%88%E7%BB%93%E8%80%85.Mythbusters.S10E03.Chi_Eng.HR-HDTV.AC3.1024X576.x264-YYeTs%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mkv|508401285|fa88f4e9f904cffa96d08cd5c4a5fad2|h=2i7c5wvqurfn7ddfhdi4xpjbyivb7qi5|/

ed2k
ed2k://|file|Duck.Dynasty.S02E01.The.Grass.&.The.Furious.1080p.WEB-DL.AAC2.0.H.264-BTN.mkv|830442056|6E6F074D8FDAECDE8F4E2188439A107C|h=5X7ZMLTEVWW5PV7NVBHGA5W7BAVNC4OX|/

ed2k contains symbol '
ed2k://|file|Believe.S01E02.Beginner's.Luck.1080p.WEB-DL.DD5.1.H.264-ECI.mkv|1697744283|E4865DE2756F053F435151C576830625|h=H5T2NIK6A7B5KENQI5AO5JUUTXSICT3P|/

ed2k contains []
ed2k://|file|[%E8%AF%B8%E7%A5%9E%E5%AD%97%E5%B9%95%E7%BB%84][NHK%E7%BA%AA%E5%BD%95%E7%89%87][%E5%A4%A7%E5%9C%B0%E9%9C%87%E6%97%B6%20%E6%B0%91%E9%97%B4%E8%AF%A5%E5%A6%82%E4%BD%95%E8%87%AA%E6%95%91][%E4%B8%AD%E6%97%A5%E5%8F%8C%E8%AF%AD%E5%AD%97%E5%B9%95][1280x720].mp4|939357813|F55CAA85A72B91780FB09BACFB168692|h=INMZ7MP2GS5UEAW4UP3EHKKG3XNPV5TO|/

magnet
magnet:?xt.1=urn:sha1:YNCKHTQCWBTRNJIV4WNAE52SJUQCZO5C&xt.2=urn:sha1:TXGCZQTH26NL6OUQAJJPFALHG2LTGBC7

magnet 2
magnet:?xt=urn:btih:d8621b178ec96d703fa28d83ad16b87904f8f4d4&dn=Arch+Linux+2013.12.01+dual&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337

magnet 3
magnet:?xt=urn:btih:ae5097941646d4fa76c9b83f0734d76787b9aaa0&dn=Suits.S03E14.720p.HDTV.x264-REMARKABLE%5Brartv%5D&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337

magnet 4
magnet:?xt=urn:btih:757fc565c56462b28b4f9c86b21ac753500eb2a7&dn=archlinux-2014.04.01-dual.iso&tr=udp://tracker.archlinux.org:6969&tr=http://tracker.archlinux.org:6969/announce

https://piratebaytorrents.info/a9758370/Rimworld_Alpha2_(Linux).9758370.TPB.torrent

shouldnt match this one
http://hackage.haskell.org/package/base-4.7.0.0/docs/Control-Arrow.html

END THIS TEST WITH A LITTLE DANCE:)
http://no.newline.at.the.end/download.txt"""

_ExpectedResult = """thunder://QUFodHRwOi8vaW0uYmFpZHUuY29tL2luc3RhbGwvQmFpZHVIaS5leGVaWg==
http://www.163.com/robots.zip
ftp://dashingdash.com/1-2.txt
http://username@www.263.com/robots.cab
http://user-name+1.23_ok:pass@www.w3c.com/spec.tar.gz
http://user:pa+ss-wo_rd1.23@www.w3c.com/1.tar.gz
http://un:pass@www.444.com:1353/robots.txt
http://www.555.com/player.exe?ab=3
http://666.com/player.exe?ab=3&cd=opq
http://71.35.264.35/测试.cab
https://1.2.3.4/【1】.zip
https://localhost:8000/test_page.zip?ab=3-5,5-6&cd=%20&callback=foo_bar
http://127.0.0.1/bar.php.zip
HtTP://test.com/foo.zIP
http://www.test.com/1.exe
http://www.test.com/1.exe?op=DOWNLOAD
ed2k://|file|The_Two_Towers-The_Purist_Edit-Trailer.avi|14997504|965c013e991ee246d63d45ea71954c4d|/
ed2k://|file|The_Two_Towers-The_Purist_Edit-Trailer.avi|14997504|965c013e991ee246d63d45ea71954c4d|/|sources,202.89.123.6:4662|/
ed2k://|file|%E6%B5%81%E8%A8%80%E7%BB%88%E7%BB%93%E8%80%85.Mythbusters.S10E03.Chi_Eng.HR-HDTV.AC3.1024X576.x264-YYeTs%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mkv|508401285|fa88f4e9f904cffa96d08cd5c4a5fad2|h=2i7c5wvqurfn7ddfhdi4xpjbyivb7qi5|/
ed2k://|file|Duck.Dynasty.S02E01.The.Grass.&.The.Furious.1080p.WEB-DL.AAC2.0.H.264-BTN.mkv|830442056|6E6F074D8FDAECDE8F4E2188439A107C|h=5X7ZMLTEVWW5PV7NVBHGA5W7BAVNC4OX|/
ed2k://|file|Believe.S01E02.Beginner's.Luck.1080p.WEB-DL.DD5.1.H.264-ECI.mkv|1697744283|E4865DE2756F053F435151C576830625|h=H5T2NIK6A7B5KENQI5AO5JUUTXSICT3P|/
ed2k://|file|[%E8%AF%B8%E7%A5%9E%E5%AD%97%E5%B9%95%E7%BB%84][NHK%E7%BA%AA%E5%BD%95%E7%89%87][%E5%A4%A7%E5%9C%B0%E9%9C%87%E6%97%B6%20%E6%B0%91%E9%97%B4%E8%AF%A5%E5%A6%82%E4%BD%95%E8%87%AA%E6%95%91][%E4%B8%AD%E6%97%A5%E5%8F%8C%E8%AF%AD%E5%AD%97%E5%B9%95][1280x720].mp4|939357813|F55CAA85A72B91780FB09BACFB168692|h=INMZ7MP2GS5UEAW4UP3EHKKG3XNPV5TO|/
magnet:?xt.1=urn:sha1:YNCKHTQCWBTRNJIV4WNAE52SJUQCZO5C&xt.2=urn:sha1:TXGCZQTH26NL6OUQAJJPFALHG2LTGBC7
magnet:?xt=urn:btih:d8621b178ec96d703fa28d83ad16b87904f8f4d4&dn=Arch+Linux+2013.12.01+dual&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337
magnet:?xt=urn:btih:ae5097941646d4fa76c9b83f0734d76787b9aaa0&dn=Suits.S03E14.720p.HDTV.x264-REMARKABLE%5Brartv%5D&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337
magnet:?xt=urn:btih:757fc565c56462b28b4f9c86b21ac753500eb2a7&dn=archlinux-2014.04.01-dual.iso&tr=udp://tracker.archlinux.org:6969&tr=http://tracker.archlinux.org:6969/announce
https://piratebaytorrents.info/a9758370/Rimworld_Alpha2_(Linux).9758370.TPB.torrent
http://no.newline.at.the.end/download.txt"""


class TestExtractUrls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extractor = mimeparser.UrlExtractor(None)
        cls.extractor.updatePatternRegex({".zip", ".cab", ".exe", ".txt", ".torrent", ".doc", ".tar.gz"})

    def test_extract(self):
        results = self.extractor.extract(testCases)

        self.assertListEqual(results, list(_ExpectedResult.strip().split("\n")))

if __name__ == "__main__":
    unittest.main()
