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
import sys
from PyQt6 import QtWidgets, QtCore
from ddg import CentralWidget
from ddg import __version__

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    QtCore.QDir.addSearchPath('icons', './icons/')

    if 'plastique' in QtWidgets.QStyleFactory().keys():
        app.setStyle(QtWidgets.QStyleFactory.create('plastique'))
    screen = app.primaryScreen()
    for s in app.screens():
        if screen.geometry().width() < s.geometry().width():
            screen = s
    main = QtWidgets.QMainWindow()
    main.setWindowTitle('DotDotGoose [v {}] - Center for Biodiversity and Conservation ( http://cbc.amnh.org )'.format(__version__))
    main.setCentralWidget(CentralWidget())
    main.show()
    main.windowHandle().setScreen(screen)
    main.resize(int(screen.geometry().width()), int(screen.geometry().height() * 0.85))

    sys.exit(app.exec())
