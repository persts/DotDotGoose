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
from ddg import CentralWidget
from PyQt6 import QtWidgets, QtCore
from ddg import __version__


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle('DotDotGoose [v {}] - Center for Biodiversity and Conservation ( http://amnh.org/cbc )'.format(__version__))
        self.setCentralWidget(CentralWidget())

        self.error_widget = QtWidgets.QTextBrowser()
        self.error_widget.setWindowTitle(self.tr('EXCEPTION DETECTED'))
        self.error_widget.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.error_widget.resize(900, 500)

        self.setMenuBar(QtWidgets.QMenuBar())
        menu = self.menuBar().addMenu(self.tr('File'))
        menu.setObjectName('File')
        menu.addAction(self.tr('Quit'), self.quit)

        menu = self.menuBar().addMenu(self.tr('Language'))
        menu.setObjectName('Language')
        menu.addAction(self.tr('English'), self.en_US)
        menu.addAction(self.tr('French'), self.fr_FR)

    def display_exception(self, error):
        self.error_widget.clear()
        for line in error:
            self.error_widget.append(line)
        self.error_widget.show()

    def en_US(self):
        settings = QtCore.QSettings("AMNH", "DotDotGoose")
        settings.setValue('locale', 'en_US')
        self.restart_message()

    def fr_FR(self):
        settings = QtCore.QSettings("AMNH", "DotDotGoose")
        settings.setValue('locale', 'fr')
        self.restart_message()

    def restart_message(self):
        QtWidgets.QMessageBox.warning(self.parent(), self.tr('Restart Required'), self.tr('You must restart the application for the language setting to be applied.'), QtWidgets.QMessageBox.StandardButton.Ok)

    def quit(self):
        self.close()
