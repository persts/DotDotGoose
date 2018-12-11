# -*- coding: utf-8 -*-
#
# Mark Count
# Copyright (C) 2018 Peter Ersts
# ersts@amnh.org
#
# --------------------------------------------------------------------------
#
# This file is part of the Mark Count application.
# Mark Count was forked from the Neural Network Image Classifier (Nenetic).
#
# Andenet is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Andenet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------------------------------------------
import sys
from PyQt5 import QtWidgets
from mc import CentralWidget

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    if 'plastique' in QtWidgets.QStyleFactory().keys():
        app.setStyle(QtWidgets.QStyleFactory.create('plastique'))
    screen = app.desktop().availableGeometry()
    main = QtWidgets.QMainWindow()
    main.setWindowTitle('Dot.Dot.Goose -- beta 2 -- Do not redistribute')
    main.setCentralWidget(CentralWidget())
    main.show()
    main.resize(int(screen.width() * .95), screen.height())
    main.move(int(screen.width() * .05) // 2, 0)

    sys.exit(app.exec_())
