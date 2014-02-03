all: libmounthelper.so
	make -C frontend

libmounthelper.so: libmounthelper.c
	gcc libmounthelper.c -m32 -o build/libmounthelper.so -fPIC -shared -ldl

clean:
	rm -f EmbedThunderManager
	rm -f ETMDaemon
	rm -f portal
	rm -f *.zip
	make -C frontend clean
