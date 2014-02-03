all:
	pyuic5 -o ui_main.py ui/main.ui
	pyuic5 -o ui_settings.py ui/settings.ui
	pyrcc5 -o resource_rc.py ui/rc/resource.qrc

clean:
	rm -f ui_*.py
	rm -f *_rc.py