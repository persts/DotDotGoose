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
import os
import sys

from .exporter import Exporter

from PyQt6 import QtCore, QtWidgets, QtGui, uic

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(__file__)
CLASS_DIALOG, _ = uic.loadUiType(os.path.join(bundle_dir, 'chip_dialog.ui'))


class ChipDialog(QtWidgets.QDialog, CLASS_DIALOG):

    def __init__(self, classes, points, directory, survey_id):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.setWindowTitle(self.tr('Export Image Chips'))
        self.setModal(True)

        self.classes = classes
        self.points = points
        self.directory = directory
        self.survey_id = survey_id
        self.width = 0
        self.height = 0

        self.exporter = QtCore.QThread()

        self.spinBoxWidth.valueChanged.connect(self.set_width)
        self.spinBoxHeight.valueChanged.connect(self.set_height)

        self.pushButtonCancel.clicked.connect(self.cancel)
        self.pushButtonExport.clicked.connect(self.export)
        self.pushButtonCancel.setIcon(QtGui.QIcon('icons:cancel.svg'))
        self.pushButtonExport.setIcon(QtGui.QIcon('icons:export.svg'))

        count = 0
        for image in self.points:
            for class_name in self.points[image]:
                count += len(self.points[image][class_name])
        self.progressBar.setRange(0, count)

    def cancel(self):
        if self.exporter.isRunning():
            self.exporter.terminate()
        else:
            self.close()

    def export(self):
        self.pushButtonCancel.setText(self.tr('Cancel'))
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr('Select Directory'), self.directory, QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if directory != '':
            if len(os.listdir(directory)) != 0:
                QtWidgets.QMessageBox.warning(self, self.tr('Target Directory'), self.tr('The target directory contains data, please select an empty directory for exporting.'))
            else:
                file_type = '.png'
                if self.radioButtonJpeg.isChecked():
                    file_type = '.jpg'
                # TODO: make this constructor parameters cleaner
                self.exporter = Exporter(self.survey_id, self.classes, self.points, self.directory, directory, self.spinBoxWidth.value(), self.spinBoxHeight.value(), file_type)
                self.exporter.finished.connect(self.finished)
                self.exporter.progress.connect(self.progressBar.setValue)
                self.exporter.start()

    def finished(self):
        self.pushButtonCancel.setText(self.tr('Close'))

    def set_height(self, value):
        self.height = value

    def set_width(self, value):
        self.width = value
