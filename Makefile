CC            = gcc
FLAGS         = -Wall -O3
PREFIX        = /opt/xware-desktop
GITHASH       = "`git rev-parse HEAD 2>/dev/null`"
SHELL         = /bin/bash

UNAME_O      := $(shell uname -o)

.PHONY: all pyqt coffee prepareXware replacePath pep8 clean install \
        prepareXwareFake replacePathFake binaryFake extensions

ifeq ($(UNAME_O),Cygwin)
    pyuic5   := pyuic5.bat
    pyrcc5   := pyrcc5.exe
    python3  := python.exe

    all: binaryFake pyqt coffee prepareXwareFake replacePathFake
else
    pyuic5   := pyuic5
    pyrcc5   := pyrcc5
    python3  := python3

    all: build/etmpatch.so build/chmns pyqt coffee prepareXware replacePath extensions
endif

binaryFake:
	mkdir -p build
	touch build/etmpatch.so
	touch build/chmns

build/etmpatch.so: src/etmpatch.c
	mkdir -p build
	$(CC) $(FLAGS) -m32 -o build/etmpatch.so -fPIC -shared -ldl src/etmpatch.c

build/chmns: src/chmns.c
	$(CC) $(FLAGS) -o build/chmns  src/chmns.c

extensions:
	make -C src/frontend/Extensions all

clean:
	# arch packaging
	rm -rf pkg

	# deb packaging
	rm -rf debian/xware-desktop
	rm -rf debian/files
	rm -rf debian/*.debhelper
	rm -rf debian/*.debhelper.log
	rm -rf debian/*.substvars

	# build
	rm -rf build
	rm -rf preparedXware

	# in-place
	find src/frontend -name "ui_*.py" -print0 | xargs -0 rm -f
	find src/frontend -name "*_rc.py" -print0 | xargs -0 rm -f
	find src -name "__pycache__" -print0 | xargs -0 rm -rf
	find src/frontend -name "*.js" -print0 | xargs -0 rm -f

	# extensions
	make -C src/frontend/Extensions clean

pyqt:
	$(pyuic5) -o src/frontend/legacy/ui_main.py     src/frontend/ui/main.ui
	$(pyuic5) -o src/frontend/legacy/ui_settings.py src/frontend/ui/settings.ui
	$(pyuic5) -o src/frontend/legacy/ui_about.py    src/frontend/ui/about.ui
	$(pyuic5) -o src/frontend/legacy/ui_scheduler.py  src/frontend/ui/scheduler.ui
	$(pyuic5) -o src/frontend/Settings/ui_quickspeedlimit.py  src/frontend/ui/quickspeedlimit.ui
	$(pyuic5) -o src/frontend/CrashReport/ui_crashreport.py  src/frontend/ui/crashreport.ui
	$(pyuic5) -o src/frontend/Widgets/ui_monitor.py  src/frontend/ui/monitor.ui
	$(pyuic5) -o src/frontend/Widgets/ui_taskproperty.py  src/frontend/ui/taskproperty.ui
	$(pyrcc5) -o src/frontend/resource_rc.py src/frontend/ui/rc/resource.qrc

pep8:
	find src -name "*.py" -not -path "src/shared/thirdparty/*" -print0 | xargs -0 pep8 --exclude "ui_*.py,*_rc.py,test_*.py" --statistics --ignore "E251,E401,E402"

coffee:
	find src -name "*.coffee" -print0 | xargs -0 coffee -bc

prepareXwareFake:
	mkdir -p preparedXware
	touch preparedXware/ETMDaemon
	touch preparedXware/EmbedThunderManager
	touch preparedXware/portal
	touch preparedXware/vod_httpserver

prepareXware:
	mkdir -p preparedXware
	cp xware/ETMDaemon           preparedXware/
	cp xware/EmbedThunderManager preparedXware/
	cp xware/portal              preparedXware/
	cp xware/vod_httpserver      preparedXware/
	chrpath --delete preparedXware/ETMDaemon
	chrpath --delete preparedXware/EmbedThunderManager
	chrpath --delete preparedXware/portal
	chrpath --delete preparedXware/vod_httpserver

replacePathFake:
	mkdir -p build
	touch build/xwared.service
	touch build/xwared.conf
	touch build/xwared.desktop

replacePath:
	mkdir -p build
	cat src/xwared.service.template | sed s,##PREFIX##,$(PREFIX), > build/xwared.service
	cat src/xwared.conf.template | sed s,##PREFIX##,$(PREFIX), > build/xwared.conf
	cat src/xwared.desktop.template | sed s,##PREFIX##,$(PREFIX), > build/xwared.desktop
	
#sudo is needed for install
install:
	install -d $(DESTDIR)$(PREFIX)
	install -d $(DESTDIR)$(PREFIX)/xware
	install -d $(DESTDIR)$(PREFIX)/xware/lib

	# xware
	install preparedXware/ETMDaemon           $(DESTDIR)$(PREFIX)/xware/lib/ETMDaemon
	install preparedXware/EmbedThunderManager $(DESTDIR)$(PREFIX)/xware/lib/EmbedThunderManager
	install preparedXware/vod_httpserver      $(DESTDIR)$(PREFIX)/xware/lib/vod_httpserver
	install preparedXware/portal              $(DESTDIR)$(PREFIX)/xware/portal

	# binary
	install build/chmns       $(DESTDIR)$(PREFIX)/chmns
	install build/etmpatch.so $(DESTDIR)$(PREFIX)/etmpatch.so

	# copy py files
	cp -R src/frontend $(DESTDIR)$(PREFIX)
	cp -R src/shared   $(DESTDIR)$(PREFIX)
	cp -R src/daemon   $(DESTDIR)$(PREFIX)

	# remove unwanted files
	rm -r              $(DESTDIR)$(PREFIX)/frontend/ui
	find $(DESTDIR)$(PREFIX) -name "*.coffee" -print0 | xargs -0 rm
	rm                 $(DESTDIR)$(PREFIX)/frontend/xware-desktop.desktop
	rm -r              $(DESTDIR)$(PREFIX)/frontend/Extensions/src
	rm -r              $(DESTDIR)$(PREFIX)/frontend/Extensions/sip
	rm                 $(DESTDIR)$(PREFIX)/frontend/Extensions/Makefile

	# icons
	install -d $(DESTDIR)/usr/share/icons/hicolor
	cp -R src/frontend/ui/icons/* $(DESTDIR)/usr/share/icons/hicolor
	rm $(DESTDIR)/usr/share/icons/hicolor/README

	# other
	install -D src/frontend/xware-desktop.desktop  $(DESTDIR)/usr/share/applications/xware-desktop.desktop
	install    build/xwared.conf    $(DESTDIR)$(PREFIX)/frontend/xwared.conf
	install    build/xwared.service $(DESTDIR)$(PREFIX)/frontend/xwared.service
	install    build/xwared.desktop $(DESTDIR)$(PREFIX)/frontend/xwared.desktop
	install -d $(DESTDIR)/usr/bin
	ln -s -f $(PREFIX)/frontend/launcher.py $(DESTDIR)/usr/bin/xware-desktop
	ln -s -f $(PREFIX)/daemon/xwared.py $(DESTDIR)$(PREFIX)/xwared

	echo -e "\n__githash__ = \"$(GITHASH)\"\n" >> $(DESTDIR)$(PREFIX)/shared/__init__.py

	# regenerate .pyo files
	find $(DESTDIR)$(PREFIX) -name "__pycache__" -print0 | xargs -0 rm -rf
	$(python3) -OO -m compileall -q $(DESTDIR)$(PREFIX)
	#fix permissions of source code
	#works just find without -print0 in newer linux system
	find -type f -name configure.py -print0 | xargs -0 chmod +x
	#chmod -R 777 *
	# fix permissions
	find $(DESTDIR) -type f -print0 | xargs -0 chmod 644
	find $(DESTDIR) -type d -print0 | xargs -0 chmod 755

	# mark executables
	chmod +x $(DESTDIR)$(PREFIX)/frontend/launcher.py
	chmod +x $(DESTDIR)$(PREFIX)/frontend/morula.py
	chmod +x $(DESTDIR)$(PREFIX)/frontend/CrashReport/CrashReportApp.py
	chmod +x $(DESTDIR)$(PREFIX)/daemon/xwared.py
	chmod +x $(DESTDIR)$(PREFIX)/xware/lib/EmbedThunderManager
	chmod +x $(DESTDIR)$(PREFIX)/xware/lib/ETMDaemon
	chmod +x $(DESTDIR)$(PREFIX)/xware/lib/vod_httpserver
	chmod +x $(DESTDIR)$(PREFIX)/xware/portal
	chmod +x $(DESTDIR)$(PREFIX)/chmns
	#add cap_sys_admin for unshare(CLONE_NEWNS) 
	setcap cap_sys_admin=eip $(DESTDIR)$(PREFIX)/chmns
