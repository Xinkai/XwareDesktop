all: DBusTypes.so

libDBusTypes.so: src/DBusTypes.cpp src/DBusTypes.hpp src/Extensions.pro
	cd src && qmake && make
	cp src/build/libDBusTypes.so* ./

DBusTypes.so: libDBusTypes.so
	cd sip && ./configure.py && make
	cp sip/DBusTypes.so ./

clean:
	rm -f *.so
	rm -f *.so.*
	rm -f *.dll

	rm -f sip/*.sbf
	rm -f sip/*.h
	rm -f sip/*.cpp
	rm -f sip/Makefile
	rm -f sip/*.o
	rm -f sip/*.so
	rm -f sip/*.so.*
	rm -f sip/*.exp
	
	rm -f src/Makefile
	rm -rf src/build
	rm -f src/*.o
	
test:
	python3 -c "import DBusTypes"
