CC            = gcc
FLAGS         = -Wall -O3
PREFIX        = /opt/xware-desktop
install_xware = install -m 764
install_exe   = install -m 775
install       = install -m 664
GITHASH       = "`git rev-parse master 2>/dev/null`"
SHELL         = /bin/bash

all: etmpatch.so permissioncheck pyqt xwarejs.js prepareXware replacePath

etmpatch.so: src/etmpatch.c
	mkdir -p build
	$(CC) $(FLAGS) -m32 -o build/etmpatch.so -fPIC -shared -ldl src/etmpatch.c

permissioncheck: src/permissioncheck.c
	mkdir -p build
	$(CC) $(FLAGS) -lmount -o build/permissioncheck src/permissioncheck.c \
	    -Xlinker -lmount

clean:
	rm -rf pkg
	rm -rf build
	rm -rf preparedXware
	find src/frontend -name "ui_*.py" -print0 | xargs -0 rm -f
	find src/frontend -name "*_rc.py" -print0 | xargs -0 rm -f
	find src -name "__pycache__" -print0 | xargs -0 rm -rf
	rm -f src/frontend/xwarejs.js

pyqt:
	pyuic5 -o src/frontend/ui_main.py     src/frontend/ui/main.ui
	pyuic5 -o src/frontend/Settings/ui_settings.py src/frontend/ui/settings.ui
	pyuic5 -o src/frontend/ui_about.py    src/frontend/ui/about.ui
	pyuic5 -o src/frontend/ui_monitor.py  src/frontend/ui/monitor.ui
	pyuic5 -o src/frontend/Schedule/ui_scheduler.py  src/frontend/ui/scheduler.ui
	pyuic5 -o src/frontend/Settings/ui_quickspeedlimit.py  src/frontend/ui/quickspeedlimit.ui
	pyuic5 -o src/frontend/CrashReport/ui_crashreport.py  src/frontend/ui/crashreport.ui
	pyrcc5 -o src/frontend/resource_rc.py src/frontend/ui/rc/resource.qrc

pep8:
	find src/frontend -name "*.py" -print0 | xargs -0 pep8 --exclude "ui_*.py,*_rc.py" --statistics --ignore "E251,E401"

xwarejs.js: src/frontend/xwarejs.coffee
	coffee -c src/frontend/xwarejs.coffee

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

install: all
	install -d -m 775                               $(DESTDIR)$(PREFIX)
	install -d -m 775                               $(DESTDIR)$(PREFIX)/xware
	install -d -m 775                               $(DESTDIR)$(PREFIX)/xware/lib
	install -d -m 775                               $(DESTDIR)$(PREFIX)/xware/cfg

	# xware
	$(install_xware) preparedXware/ETMDaemon           $(DESTDIR)$(PREFIX)/xware/lib/ETMDaemon
	$(install_xware) preparedXware/EmbedThunderManager $(DESTDIR)$(PREFIX)/xware/lib/EmbedThunderManager
	$(install_xware) preparedXware/vod_httpserver      $(DESTDIR)$(PREFIX)/xware/lib/vod_httpserver
	$(install_xware) preparedXware/portal              $(DESTDIR)$(PREFIX)/xware/portal

	# binary
	$(install_exe)     build/permissioncheck           $(DESTDIR)$(PREFIX)/permissioncheck
	$(install_xware)   build/etmpatch.so               $(DESTDIR)$(PREFIX)/etmpatch.so

	# copy py files
	cp -R src/frontend $(DESTDIR)$(PREFIX)
	cp -R src/shared   $(DESTDIR)$(PREFIX)
	cp -R src/daemon   $(DESTDIR)$(PREFIX)

	# remove unwanted files
	find $(DESTDIR)$(PREFIX) -name "__pycache__" -print0 | xargs -0 rm -rf
	rm -r              $(DESTDIR)$(PREFIX)/frontend/ui
	rm -r              $(DESTDIR)$(PREFIX)/frontend/tests
	rm                 $(DESTDIR)$(PREFIX)/frontend/xwarejs.coffee
	rm                 $(DESTDIR)$(PREFIX)/frontend/xware-desktop.desktop
	find $(DESTDIR)$(PREFIX)/frontend -type f -print0 | xargs -0 chmod 664
	find $(DESTDIR)$(PREFIX)/frontend -type d -print0 | xargs -0 chmod 775

	# mark executables
	chmod 775          $(DESTDIR)$(PREFIX)/frontend/launcher.py
	chmod 775          $(DESTDIR)$(PREFIX)/frontend/CrashReport/CrashReportApp.py
	chmod 775          $(DESTDIR)$(PREFIX)/daemon/xwared.py

	# icons
	install -d $(DESTDIR)/usr/share/icons/hicolor
	cp -R xware/icons/* $(DESTDIR)/usr/share/icons/hicolor

	# other
	install    -m 644 src/frontend/ui/rc/thunder.ico      $(DESTDIR)$(PREFIX)/frontend/thunder.ico
	install -D -m 644 src/frontend/xware-desktop.desktop  $(DESTDIR)/usr/share/applications/xware-desktop.desktop
	install -d $(DESTDIR)/usr/bin
	ln -s $(PREFIX)/frontend/launcher.py $(DESTDIR)/usr/bin/xware-desktop
	ln -s $(PREFIX)/daemon/xwared.py $(DESTDIR)$(PREFIX)/xwared

	echo -e "\n__githash__ = \"$(GITHASH)\"\n" >> $(DESTDIR)$(PREFIX)/shared/__init__.py
