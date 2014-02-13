all: libmounthelper.so xwared permissioncheck
	make -C frontend

libmounthelper.so: libmounthelper.c
	mkdir -p build
	gcc -m32 -o build/libmounthelper.so -fPIC -shared -ldl -Wall -O3 libmounthelper.c

xwared: xwared.c xwared.h
	gcc -m32 `pkg-config --cflags --libs glib-2.0` -o build/xwared -pthread -Wall -O3 xwared.c

permissioncheck: permissioncheck.c
	mkdir -p build
	gcc -lmount -o build/permissioncheck -Wall -O3 permissioncheck.c

clean:
	rm -rf build
	make -C frontend clean
