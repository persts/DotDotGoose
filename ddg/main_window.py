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
from PyQt6 import QtWidgets, QtCore, QtGui
from ddg import AboutDialog
from ddg import __version__


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle('DotDotGoose [v {}]'.format(__version__))
        self.setWindowIcon(QtGui.QIcon("icons:ddg.png"))
        self.setCentralWidget(CentralWidget())
        self.about_dialog = AboutDialog(self)

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
        menu.addAction(self.tr('Chinese (Mandarin)'), self.zh_Hans_CN)
        menu.addAction(self.tr('English'), self.en_US)
        menu.addAction(self.tr('French'), self.fr_FR)
        menu.addAction(self.tr('Spanish'), self.es_CO)
        menu.addAction(self.tr('Vietnamese'), self.vi_VN)

        self.menuBar().addSeparator()

        self.menuBar().addAction(self.tr('About'), self.about_dialog.show)

    def closeEvent(self, event):
        if self.centralWidget().canvas.dirty_data_check():
            event.accept()
        else:
            event.ignore()

    def display_exception(self, error):
        self.error_widget.clear()
        for line in error:
            self.error_widget.append(line)
        self.error_widget.show()

    def en_US(self):
        settings = QtCore.QSettings("AMNH", "DotDotGoose")
        settings.setValue('locale', 'en_US')
        self.restart_message()

    def es_CO(self):
        settings = QtCore.QSettings("AMNH", "DotDotGoose")
        settings.setValue('locale', 'es_CO')
        self.restart_message()

    def fr_FR(self):
        settings = QtCore.QSettings("AMNH", "DotDotGoose")
        settings.setValue('locale', 'fr')
        self.restart_message()

    def vi_VN(self):
        settings = QtCore.QSettings("AMNH", "DotDotGoose")
        settings.setValue('locale', 'vi_VN')
        self.restart_message()

    def zh_Hans_CN(self):
        settings = QtCore.QSettings("AMNH", "DotDotGoose")
        settings.setValue('locale', 'zh_Hans_CN')
        self.restart_message()

    def restart_message(self):
        QtWidgets.QMessageBox.warning(self, self.tr('Restart Required'), self.tr('You must restart the application for the language setting to be applied.'), QtWidgets.QMessageBox.StandardButton.Ok)

    def quit(self):
        self.close()
