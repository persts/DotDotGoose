# -*- coding: utf-8 -*-
#
# DotDotGoose
# Author: Peter Ersts (ersts@amnh.org)
#
# --------------------------------------------------------------------------
#
# This file is part of the DotDotGoose application.
# DotDotGoose was forked from the Neural Network Image Classifier (Nenetic).
#
# DotDotGoose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DotDotGoose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------------------------------------------
from PyQt6 import QtWidgets, QtCore


class BoxText(QtWidgets.QTextEdit):
    update = QtCore.pyqtSignal(str, str)

    def __init__(self, parent):
        QtWidgets.QTextEdit.__init__(self, parent)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.fire)

    def fire(self):
        self.update.emit(self.parent().objectName(), self.toPlainText())
        self.timer.stop()

    def keyPressEvent(self, event):
        if self.timer.isActive():
            self.timer.stop()
            self.timer.setInterval(1000)
            self.timer.start()
        else:
            self.timer.start()
        QtWidgets.QTextEdit.keyPressEvent(self, event)

    def load_data(self, data):
        key = self.parent().objectName()
        if key in data:
            self.setText(data[key])


class LineText(QtWidgets.QLineEdit):
    update = QtCore.pyqtSignal(str, str)

    def __init__(self, parent):
        QtWidgets.QTextEdit.__init__(self, parent)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.fire)

    def fire(self):
        self.update.emit(self.parent().objectName(), self.text())
        self.timer.stop()

    def keyPressEvent(self, event):
        if self.timer.isActive():
            self.timer.stop()
            self.timer.setInterval(1000)
            self.timer.start()
        else:
            self.timer.start()
        QtWidgets.QLineEdit.keyPressEvent(self, event)

    def load_data(self, data):
        key = self.parent().objectName()
        if key in data:
            self.setText(data[key])
