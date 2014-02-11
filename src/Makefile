all: libmounthelper.so xwared
	make -C frontend

libmounthelper.so: libmounthelper.c
	mkdir -p build
	gcc -m32 -o build/libmounthelper.so -fPIC -shared -ldl -Wall -O3 libmounthelper.c

xwared: xwared.c xwared.h
	gcc -m32 `pkg-config --cflags --libs glib-2.0` -o build/xwared -pthread -Wall -O3 xwared.c

clean:
	rm -f EmbedThunderManager
	rm -f ETMDaemon
	rm -f portal
	rm -f *.zip
	make -C frontend clean
