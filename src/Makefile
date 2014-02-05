all: libmounthelper.so daemon
	make -C frontend

libmounthelper.so: libmounthelper.c
	mkdir -p build
	gcc -m32 -o build/libmounthelper.so -fPIC -shared -ldl -Wall libmounthelper.c

daemon: daemon.c
	gcc -m32 -o build/daemon -pthread -Wall daemon.c

clean:
	rm -f EmbedThunderManager
	rm -f ETMDaemon
	rm -f portal
	rm -f *.zip
	make -C frontend clean
