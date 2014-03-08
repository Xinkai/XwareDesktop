CC          = gcc
FLAGS       = -Wall -O3
PREFIX      = /opt/xware_desktop
install_exe = install -m 775
install     = install -m 664

all: libmounthelper.so xwared permissioncheck pyqt xwarejs.js prepareXware

libmounthelper.so: src/libmounthelper.c
	mkdir -p build
	$(CC) $(FLAGS) -m32 -o build/libmounthelper.so -fPIC -shared -ldl src/libmounthelper.c

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

pyqt:
	pyuic5 -o src/frontend/ui_main.py     src/frontend/ui/main.ui
	pyuic5 -o src/frontend/ui_settings.py src/frontend/ui/settings.ui
	pyuic5 -o src/frontend/ui_about.py    src/frontend/ui/about.ui
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
	install -d -m 775                               $(DESTDIR)$(PREFIX)/frontend

	$(install_exe) -D preparedXware/ETMDaemon             $(DESTDIR)$(PREFIX)/xware/lib/ETMDaemon
	$(install_exe) -D preparedXware/EmbedThunderManager   $(DESTDIR)$(PREFIX)/xware/lib/EmbedThunderManager
	$(install_exe)    preparedXware/portal                $(DESTDIR)$(PREFIX)/xware/portal

	$(install_exe) build/* $(DESTDIR)$(PREFIX)

	cp -R src/frontend $(DESTDIR)$(PREFIX)
	rm -rf             $(DESTDIR)$(PREFIX)/frontend/__pycache__
	rm -rf             $(DESTDIR)$(PREFIX)/frontend/ui
	rm -f              $(DESTDIR)$(PREFIX)/frontend/xwarejs.coffee
	rm -f              $(DESTDIR)$(PREFIX)/frontend/Makefile
	chmod 664          $(DESTDIR)$(PREFIX)/frontend/*
	chmod +x           $(DESTDIR)$(PREFIX)/frontend/launcher.py

	install -D     src/xwared.service                   $(DESTDIR)/usr/lib/systemd/system/xwared.service
	install -D -m 664 src/frontend/ui/rc/thunder.ico    $(DESTDIR)$(PREFIX)/frontend/thunder.ico
	install -D     src/frontend/xware_desktop.desktop   $(DESTDIR)/usr/share/applications/xware_desktop.desktop
