# -*- coding: utf-8 -*-

import unittest
import mimeparser

testCases = """
迅雷专链
thunder://QUFodHRwOi8vaW0uYmFpZHUuY29tL2luc3RhbGwvQmFpZHVIaS5leGVaWg==

一般的文件
http://www.163.com/robots.zip

包含用户名
http://username@www.263.com/robots.cab

包含中文用户名、密码 复合扩展名
http://用户:pass@www.w3c.com/spec.tar.gz

包含用户名、密码、端口
http://un:pass@www.444.com:1353/robots.txt

一个参数
http://www.555.com/player.wmv?ab=3

多个参数
http://666.com/player.mp3?ab=3&cd=opq

ip地址、中文路径名
http://71.35.264.35/测试.7z

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

url frags
http://www.test.com/1.exe?op=DOWNLOAD#foo

正常文本
锄禾日当午 汗滴禾下土 谁知盘中餐 粒粒皆辛苦

HTML
<a href="http://10.5.3.2/archive.zip">Download</a>

ed2k
ed2k://|file|The_Two_Towers-The_Purist_Edit-Trailer.avi|14997504|965c013e991ee246d63d45ea71954c4d|/

ed2k with additional data
ed2k://|file|The_Two_Towers-The_Purist_Edit-Trailer.avi|14997504|965c013e991ee246d63d45ea71954c4d|/|sources,202.89.123.6:4662|/

another ed2k
ed2k://|file|%E6%B5%81%E8%A8%80%E7%BB%88%E7%BB%93%E8%80%85.Mythbusters.S10E03.Chi_Eng.HR-HDTV.AC3.1024X576.x264-YYeTs%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mkv|508401285|fa88f4e9f904cffa96d08cd5c4a5fad2|h=2i7c5wvqurfn7ddfhdi4xpjbyivb7qi5|/

magnet
magnet:?xt.1=urn:sha1:YNCKHTQCWBTRNJIV4WNAE52SJUQCZO5C&xt.2=urn:sha1:TXGCZQTH26NL6OUQAJJPFALHG2LTGBC7

magnet 2
magnet:?xt=urn:btih:d8621b178ec96d703fa28d83ad16b87904f8f4d4&dn=Arch+Linux+2013.12.01+dual&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337

magnet 3
magnet:?xt=urn:btih:ae5097941646d4fa76c9b83f0734d76787b9aaa0&dn=Suits.S03E14.720p.HDTV.x264-REMARKABLE%5Brartv%5D&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337

END THIS TEST WITH A LITTLE DANCE:)
"""

class TestExtractUrls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extractor = mimeparser.UrlExtractor(None)
        cls.extractor.updatePatternRegex({".zip", ".cab", ".exe", ".txt"})

    def test_extract(self):
        results = self.extractor.extract(testCases)

        self.assertListEqual(results, list(
"""thunder://QUFodHRwOi8vaW0uYmFpZHUuY29tL2luc3RhbGwvQmFpZHVIaS5leGVaWg==
http://www.163.com/robots.zip
http://username@www.263.com/robots.cab
http://un:pass@www.444.com:1353/robots.txt
https://localhost:8000/test_page.zip?ab=3-5,5-6&cd=%20&callback=foo_bar
http://106.20.35.62/1.zip
http://127.0.0.1/bar.zip
http://127.0.0.1/bar.php.zip
HtTP://test.com/foo.zIP
http://www.test.com/1.exe?op=DOWNLOAD
http://10.5.3.2/archive.zip
ed2k://|file|The_Two_Towers-The_Purist_Edit-Trailer.avi|14997504|965c013e991ee246d63d45ea71954c4d|/
ed2k://|file|The_Two_Towers-The_Purist_Edit-Trailer.avi|14997504|965c013e991ee246d63d45ea71954c4d|/|sources,202.89.123.6:4662|/
ed2k://|file|%E6%B5%81%E8%A8%80%E7%BB%88%E7%BB%93%E8%80%85.Mythbusters.S10E03.Chi_Eng.HR-HDTV.AC3.1024X576.x264-YYeTs%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mkv|508401285|fa88f4e9f904cffa96d08cd5c4a5fad2|h=2i7c5wvqurfn7ddfhdi4xpjbyivb7qi5|/
magnet:?xt.1=urn:sha1:YNCKHTQCWBTRNJIV4WNAE52SJUQCZO5C&xt.2=urn:sha1:TXGCZQTH26NL6OUQAJJPFALHG2LTGBC7
magnet:?xt=urn:btih:d8621b178ec96d703fa28d83ad16b87904f8f4d4&dn=Arch+Linux+2013.12.01+dual&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337
magnet:?xt=urn:btih:ae5097941646d4fa76c9b83f0734d76787b9aaa0&dn=Suits.S03E14.720p.HDTV.x264-REMARKABLE%5Brartv%5D&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337
""".strip().split("\n")))

if __name__=="__main__":
    unittest.main()