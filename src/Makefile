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
	$(CC) $(FLAGS) -m32 `pkg-config --cflags --libs glib-2.0` -o build/xwared -pthread \
	    xwared.c -Xlinker `pkg-config --cflags --libs glib-2.0`

permissioncheck: permissioncheck.c
	mkdir -p build
	$(CC) $(FLAGS) -lmount -o build/permissioncheck permissioncheck.c

clean:
	rm -rf build
	make -C frontend clean

install: all
	install -d -m 775                               $(DEST_DIR)$(PREFIX)
	install -d -m 775                               $(DEST_DIR)$(PREFIX)/xware
	install -d -m 775                               $(DEST_DIR)$(PREFIX)/xware/lib
	install -d -m 775                               $(DEST_DIR)$(PREFIX)/frontend

	$(install_exe) -D ../xware/ETMDaemon            $(DEST_DIR)$(PREFIX)/xware/lib/ETMDaemon
	$(install_exe) -D ../xware/EmbedThunderManager  $(DEST_DIR)$(PREFIX)/xware/lib/EmbedThunderManager
	$(install_exe) ../xware/portal                  $(DEST_DIR)$(PREFIX)/xware/portal

	$(install_exe) build/* $(DEST_DIR)$(PREFIX)

	cp -R frontend $(DEST_DIR)$(PREFIX)
	rm -rf         $(DEST_DIR)$(PREFIX)/frontend/{__pycache__,ui,xwarejs.coffee,Makefile}
	chmod -R 664   $(DEST_DIR)$(PREFIX)/frontend/*
	chmod +x       $(DEST_DIR)$(PREFIX)/frontend/launcher.py

	install -D     xwared.service                   $(DEST_DIR)/usr/lib/systemd/system/xwared.service
	install -D -m 664 frontend/ui/rc/thunder.ico    $(DEST_DIR)$(PREFIX)/frontend/thunder.ico
	install -D     frontend/xware_desktop.desktop   $(DEST_DIR)/usr/share/applications/xware_desktop.desktop
