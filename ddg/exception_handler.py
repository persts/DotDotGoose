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
import traceback
from PyQt6 import QtCore
DEBUG = False


class ExceptionHandler(QtCore.QObject):
    exception = QtCore.pyqtSignal(list)

    def __init__(self):
        QtCore.QObject.__init__(self)
        sys.excepthook = self.handle_exception

    def handle_exception(self, ex_type, ex_value, ex_traceback):
        error = []
        error.append(ex_type.__name__)
        for line in traceback.format_tb(ex_traceback):
            error.append(line)
        self.exception.emit(error)

        if DEBUG:
            for line in error:
                print(line)
