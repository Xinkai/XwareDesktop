CC            = gcc
FLAGS         = -Wall -O3
PREFIX        = /opt/xware_desktop
install_xware = install -m 764
install_exe   = install -m 775
install       = install -m 664

all: etmpatch.so xwared permissioncheck pyqt xwarejs.js prepareXware

etmpatch.so: src/etmpatch.c
	mkdir -p build
	$(CC) $(FLAGS) -m32 -o build/etmpatch.so -fPIC -shared -ldl src/etmpatch.c

xwared: src/xwared.c src/xwared.h
	mkdir -p build
	$(CC) $(FLAGS) -m32 `pkg-config --cflags --libs glib-2.0` -o build/xwared -pthread src/xwared.c \
	    -Xlinker -lglib-2.0

permissioncheck: src/permissioncheck.c
	mkdir -p build
	$(CC) $(FLAGS) -lmount -o build/permissioncheck src/permissioncheck.c \
	    -Xlinker -lmount

clean:
	rm -rf pkg
	rm -rf build
	rm -rf preparedXware
	rm -f src/frontend/ui_*.py
	rm -f src/frontend/*_rc.py
	rm -f src/frontend/xwarejs.js
	rm -rf src/frontend/__pycache__
	rm -rf src/frontend/*/__pycache__

pyqt:
	pyuic5 -o src/frontend/ui_main.py     src/frontend/ui/main.ui
	pyuic5 -o src/frontend/ui_settings.py src/frontend/ui/settings.ui
	pyuic5 -o src/frontend/ui_about.py    src/frontend/ui/about.ui
	pyuic5 -o src/frontend/ui_monitor.py  src/frontend/ui/monitor.ui
	pyrcc5 -o src/frontend/resource_rc.py src/frontend/ui/rc/resource.qrc

xwarejs.js: src/frontend/xwarejs.coffee
	coffee -c src/frontend/xwarejs.coffee

prepareXware:
	mkdir -p preparedXware
	cp xware/ETMDaemon           preparedXware/
	cp xware/EmbedThunderManager preparedXware/
	cp xware/portal              preparedXware/
	chrpath --delete preparedXware/ETMDaemon
	chrpath --delete preparedXware/EmbedThunderManager
	chrpath --delete preparedXware/portal

install: all
	install -d -m 775                               $(DESTDIR)$(PREFIX)
	install -d -m 775                               $(DESTDIR)$(PREFIX)/xware
	install -d -m 775                               $(DESTDIR)$(PREFIX)/xware/lib
	install -d -m 775                               $(DESTDIR)$(PREFIX)/xware/cfg

	# xware
	$(install_xware) preparedXware/ETMDaemon           $(DESTDIR)$(PREFIX)/xware/lib/ETMDaemon
	$(install_xware) preparedXware/EmbedThunderManager $(DESTDIR)$(PREFIX)/xware/lib/EmbedThunderManager
	$(install_xware) preparedXware/portal              $(DESTDIR)$(PREFIX)/xware/portal

	# binary
	$(install_exe)     build/permissioncheck           $(DESTDIR)$(PREFIX)/permissioncheck
	$(install_xware)   build/etmpatch.so               $(DESTDIR)$(PREFIX)/etmpatch.so
	$(install_xware)   build/xwared                    $(DESTDIR)$(PREFIX)/xwared

	# frontend
	cp -R src/frontend $(DESTDIR)$(PREFIX)
	rm -rf             $(DESTDIR)$(PREFIX)/frontend/__pycache__
	rm -rf             $(DESTDIR)$(PREFIX)/frontend/*/__pycache__
	rm -r              $(DESTDIR)$(PREFIX)/frontend/ui
	rm -r              $(DESTDIR)$(PREFIX)/frontend/tests
	rm                 $(DESTDIR)$(PREFIX)/frontend/xwarejs.coffee
	rm                 $(DESTDIR)$(PREFIX)/frontend/xware_desktop.desktop
	find $(DESTDIR)$(PREFIX)/frontend -type f -print0 | xargs -0 chmod 664
	find $(DESTDIR)$(PREFIX)/frontend -type d -print0 | xargs -0 chmod 775
	chmod 775          $(DESTDIR)$(PREFIX)/frontend/launcher.py

	# other
	install    -m 644 src/frontend/ui/rc/thunder.ico      $(DESTDIR)$(PREFIX)/frontend/thunder.ico
	install -D -m 644 src/frontend/xware_desktop.desktop  $(DESTDIR)/usr/share/applications/xware_desktop.desktop
