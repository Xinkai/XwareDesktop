CC            = gcc
FLAGS         = -Wall -O3
PREFIX        = /opt/xware-desktop
GITHASH       = "`git rev-parse master 2>/dev/null`"
SHELL         = /bin/bash

all: etmpatch.so chmns pyqt coffee prepareXware replacePath

etmpatch.so: src/etmpatch.c
	mkdir -p build
	$(CC) $(FLAGS) -m32 -o build/etmpatch.so -fPIC -shared -ldl src/etmpatch.c

chmns: src/chmns.c
	$(CC) $(FLAGS) -o build/chmns src/chmns.c

clean:
	rm -rf pkg
	rm -rf build
	rm -rf preparedXware
	find src/frontend -name "ui_*.py" -print0 | xargs -0 rm -f
	find src/frontend -name "*_rc.py" -print0 | xargs -0 rm -f
	find src -name "__pycache__" -print0 | xargs -0 rm -rf
	find src/frontend -name "*.js" -print0 | xargs -0 rm -f

pyqt:
	pyuic5 -o src/frontend/ui_main.py     src/frontend/ui/main.ui
	pyuic5 -o src/frontend/Settings/ui_settings.py src/frontend/ui/settings.ui
	pyuic5 -o src/frontend/ui_about.py    src/frontend/ui/about.ui
	pyuic5 -o src/frontend/ui_monitor.py  src/frontend/ui/monitor.ui
	pyuic5 -o src/frontend/Schedule/ui_scheduler.py  src/frontend/ui/scheduler.ui
	pyuic5 -o src/frontend/Settings/ui_quickspeedlimit.py  src/frontend/ui/quickspeedlimit.ui
	pyuic5 -o src/frontend/CrashReport/ui_crashreport.py  src/frontend/ui/crashreport.ui
	pyuic5 -o src/frontend/Widgets/ui_taskproperty.py  src/frontend/ui/taskproperty.ui
	pyrcc5 -o src/frontend/resource_rc.py src/frontend/ui/rc/resource.qrc

pep8:
	find src -name "*.py" -print0 | xargs -0 pep8 --exclude "ui_*.py,*_rc.py,test_*.py" --statistics --ignore "E251,E401"

coffee:
	find src -name "*.coffee" -print0 | xargs -0 coffee -bc

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

replacePath:
	mkdir -p build
	cat src/xwared.service.template | sed s,##PREFIX##,$(PREFIX), > build/xwared.service
	cat src/xwared.conf.template | sed s,##PREFIX##,$(PREFIX), > build/xwared.conf
	cat src/xwared.desktop.template | sed s,##PREFIX##,$(PREFIX), > build/xwared.desktop

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
	rm -r              $(DESTDIR)$(PREFIX)/frontend/tests
	find $(DESTDIR)$(PREFIX) -name "*.coffee" -print0 | xargs -0 rm
	rm                 $(DESTDIR)$(PREFIX)/frontend/xware-desktop.desktop

	# icons
	install -d $(DESTDIR)/usr/share/icons/hicolor
	cp -R xware/icons/* $(DESTDIR)/usr/share/icons/hicolor

	# other
	install -D src/frontend/xware-desktop.desktop  $(DESTDIR)/usr/share/applications/xware-desktop.desktop
	install    build/xwared.conf    $(DESTDIR)$(PREFIX)/frontend/xwared.conf
	install    build/xwared.service $(DESTDIR)$(PREFIX)/frontend/xwared.service
	install    build/xwared.desktop $(DESTDIR)$(PREFIX)/frontend/xwared.desktop
	install -d $(DESTDIR)/usr/bin
	ln -s $(PREFIX)/frontend/launcher.py $(DESTDIR)/usr/bin/xware-desktop
	ln -s $(PREFIX)/daemon/xwared.py $(DESTDIR)$(PREFIX)/xwared

	echo -e "\n__githash__ = \"$(GITHASH)\"\n" >> $(DESTDIR)$(PREFIX)/shared/__init__.py

	# regenerate .pyo files
	find $(DESTDIR)$(PREFIX) -name "__pycache__" -print0 | xargs -0 rm -rf
	python3 -OO -m compileall -q $(DESTDIR)$(PREFIX)

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
