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
from PyQt5 import QtCore, QtWidgets, QtGui, uic

from ddg import Canvas
from ddg import PointWidget
from ddg.fields import BoxText, LineText

# from .ui_central_widget import Ui_central as CLASS_DIALOG
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(__file__)
CLASS_DIALOG, _ = uic.loadUiType(os.path.join(bundle_dir, 'central_widget.ui'))


class CentralWidget(QtWidgets.QDialog, CLASS_DIALOG):

    load_custom_data = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.canvas = Canvas()

        self.point_widget = PointWidget(self.canvas, self)
        self.findChild(QtWidgets.QFrame, 'framePointWidget').layout().addWidget(self.point_widget)
        self.point_widget.hide_custom_fields.connect(self.hide_custom_fields)
        self.point_widget.saving.connect(self.display_quick_save)
        self.point_widget.class_selection_changed.connect(self.display_attributes)

        self.save_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+S")), self)  # quick save using Ctrl+S
        self.save_shortcut.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.save_shortcut.activated.connect(self.point_widget.quick_save)

        self.up_arrow = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Up), self)
        self.up_arrow.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.up_arrow.activated.connect(self.point_widget.previous)

        self.down_arrow = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Down), self)
        self.down_arrow.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.down_arrow.activated.connect(self.point_widget.next)

        # same as arrows but conventient for right handed people
        self.up_arrow = QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("W")), self)
        self.up_arrow.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.up_arrow.activated.connect(self.point_widget.previous)

        self.down_arrow = QtWidgets.QShortcut(QtGui.QKeySequence(self.tr("S")), self)
        self.down_arrow.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.down_arrow.activated.connect(self.point_widget.next)

        self.graphicsView.setScene(self.canvas)
        self.graphicsView.drop_complete.connect(self.canvas.load)
        self.graphicsView.region_selected.connect(self.canvas.select_points)
        self.graphicsView.delete_selection.connect(self.canvas.delete_selected_points)
        self.graphicsView.relabel_selection.connect(self.canvas.relabel_selected_points)
        self.graphicsView.toggle_points.connect(self.point_widget.checkBoxDisplayPoints.toggle)
        self.graphicsView.toggle_grid.connect(self.point_widget.checkBoxDisplayGrid.toggle)
        # self.graphicsView.switch_class.connect(self.point_widget.set_active_class)

        self.graphicsView.add_point.connect(self.canvas.add_point)
        self.graphicsView.display_pointer_coordinates.connect(self.display_pointer_coordinates)
        self.canvas.image_loaded.connect(self.graphicsView.image_loaded)
        self.canvas.directory_set.connect(self.display_working_directory)

        # Image data fields
        self.canvas.image_loaded.connect(self.display_coordinates)
        self.canvas.image_loaded.connect(self.display_attributes)
        # self.canvas.fields_updated.connect(self.display_attributes)
        self.lineEditX.textEdited.connect(self.update_coordinates)
        self.lineEditY.textEdited.connect(self.update_coordinates)

        self.lineEdit_attributes = {}
        self.lineEdit_attributes["Marking"] = self.lineEdit_marking
        self.lineEdit_attributes["Partnumber"] = self.lineEdit_partnumber
        self.lineEdit_attributes["Manufacturer"] = self.lineEdit_manufacturer
        self.lineEdit_attributes["Package"] = self.lineEdit_package
        for k, lineEdit in self.lineEdit_attributes.items():
            lineEdit.textEdited.connect(self.update_attributes)

        self.pushButtonFolder.clicked.connect(self.select_folder)
        self.pushButtonZoomOut.clicked.connect(self.graphicsView.zoom_out)
        self.pushButtonZoomIn.clicked.connect(self.graphicsView.zoom_in)

        self.quick_save_frame = QtWidgets.QFrame(self.graphicsView)
        self.quick_save_frame.setStyleSheet("QFrame { background: #4caf50;color: #FFF;font-weight: bold}")
        self.quick_save_frame.setLayout(QtWidgets.QHBoxLayout())
        self.quick_save_frame.layout().addWidget(QtWidgets.QLabel('Saving...'))
        self.quick_save_frame.setGeometry(3, 3, 100, 35)
        self.quick_save_frame.hide()

    def display_pointer_coordinates(self, point):
        text = "{:d}, {:d}".format(int(point.x()), int(point.y()))
        self.posLabel.setText(text)


    def resizeEvent(self, theEvent):
        self.graphicsView.resize_image()


    def display_coordinates(self, directory, image):
        if image in self.canvas.coordinates:
            self.lineEditX.setText(self.canvas.coordinates[image]['x'])
            self.lineEditY.setText(self.canvas.coordinates[image]['y'])
        else:
            self.lineEditX.setText('')
            self.lineEditY.setText('')

    def display_attributes(self):
        if self.canvas.current_class_name is None:
            for _, lineEdit in self.lineEdit_attributes.items():
                lineEdit.setText("")
        else:
            for k, lineEdit in self.lineEdit_attributes.items():
                lineEdit.setText(self.canvas.class_attributes[self.canvas.current_class_name][k])
                
    def display_working_directory(self, directory):
        self.labelWorkingDirectory.setText(directory)

    def display_quick_save(self):
        self.quick_save_frame.show()
        QtCore.QTimer.singleShot(500, self.quick_save_frame.hide)

    def hide_custom_fields(self, hide):
        if hide is True:
            self.frameCustomField.hide()
        else:
            self.frameCustomField.show()

    def select_folder(self):
        name = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select image folder', self.canvas.directory)
        if name != '':
            self.canvas.load([QtCore.QUrl('file:{}'.format(name))])

    def update_coordinates(self, text):
        x = self.lineEditX.text()
        y = self.lineEditY.text()
        self.canvas.save_coordinates(x, y)
        
    def update_attributes(self, text):
        for k, lineEdit in self.lineEdit_attributes.items():
            value = lineEdit.text()
            self.canvas.set_component_attribute(k, value)