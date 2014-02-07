all: pyqt xwarejs.js

pyqt:
	pyuic5 -o ui_main.py ui/main.ui
	pyuic5 -o ui_settings.py ui/settings.ui
	pyuic5 -o ui_about.py ui/about.ui
	pyrcc5 -o resource_rc.py ui/rc/resource.qrc


xwarejs.js: xwarejs.coffee
	coffee -c xwarejs.coffee

clean:
	rm -f ui_*.py
	rm -f *_rc.py
	rm -f xwarejs.js