CC          = gcc
FLAGS       = -Wall -O3
PREFIX      = /opt/xware_desktop
install_exe = install -m 775
install     = install -m 664

all: libmounthelper.so xwared permissioncheck
	make -C frontend

libmounthelper.so: libmounthelper.c
	mkdir -p build
	$(CC) $(FLAGS) -m32 -o build/libmounthelper.so -fPIC -shared -ldl libmounthelper.c

xwared: xwared.c xwared.h
	$(CC) $(FLAGS) -m32 `pkg-config --cflags --libs glib-2.0` -o build/xwared -pthread xwared.c \
	    -Xlinker -lglib-2.0

permissioncheck: permissioncheck.c
	mkdir -p build
	$(CC) $(FLAGS) -lmount -o build/permissioncheck permissioncheck.c \
	    -Xlinker -lmount

clean:
	rm -rf build
	make -C frontend clean

install: all
	install -d -m 775                               $(DESTDIR)$(PREFIX)
	install -d -m 775                               $(DESTDIR)$(PREFIX)/xware
	install -d -m 775                               $(DESTDIR)$(PREFIX)/xware/lib
	install -d -m 775                               $(DESTDIR)$(PREFIX)/frontend

	$(install_exe) -D ../xware/ETMDaemon            $(DESTDIR)$(PREFIX)/xware/lib/ETMDaemon
	$(install_exe) -D ../xware/EmbedThunderManager  $(DESTDIR)$(PREFIX)/xware/lib/EmbedThunderManager
	$(install_exe) ../xware/portal                  $(DESTDIR)$(PREFIX)/xware/portal

	$(install_exe) build/* $(DESTDIR)$(PREFIX)

	cp -R frontend $(DESTDIR)$(PREFIX)
	rm -rf         $(DESTDIR)$(PREFIX)/frontend/__pycache__
	rm -rf         $(DESTDIR)$(PREFIX)/frontend/ui
	rm -f          $(DESTDIR)$(PREFIX)/frontend/xwarejs.coffee
	rm -f          $(DESTDIR)$(PREFIX)/frontend/Makefile
	chmod 664      $(DESTDIR)$(PREFIX)/frontend/*
	chmod +x       $(DESTDIR)$(PREFIX)/frontend/launcher.py

	install -D     xwared.service                   $(DESTDIR)/usr/lib/systemd/system/xwared.service
	install -D -m 664 frontend/ui/rc/thunder.ico    $(DESTDIR)$(PREFIX)/frontend/thunder.ico
	install -D     frontend/xware_desktop.desktop   $(DESTDIR)/usr/share/applications/xware_desktop.desktop
