cd .\ddg\ui

pyuic5 central_widget.ui -o central_widget_ui.py
pyuic5 chip_dialog.ui -o chip_dialog_ui.py
pyuic5 point_widget.ui -o point_widget_ui.py

cd ..\..

pyinstaller main.py --onefile --clean --windowed