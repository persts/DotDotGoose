# -*- coding: utf-8 -*-
#
# Dot-Dot-Goose
# Copyright (C) 2018 Peter Ersts
# ersts@amnh.org
#
# --------------------------------------------------------------------------
#
# This file is part of the Dot-Dot-Goose application.
# Dot-Dot-Goose was forked from the Neural Network Image Classifier (Nenetic).
#
# Dot-Dot-Goose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dot-Dot-Goose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------------------------------------------
import os
from PyQt5 import QtCore, QtWidgets, uic

from ddg import Canvas
from ddg import PointWidget
from ddg.fields import BoxText, LineText

# from .ui_central_widget import Ui_central as CLASS_DIALOG
CLASS_DIALOG, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'central_widget.ui'))


class CentralWidget(QtWidgets.QDialog, CLASS_DIALOG):

    load_custom_data = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.canvas = Canvas()

        self.point_widget = PointWidget(self.canvas, self)
        self.findChild(QtWidgets.QGroupBox, 'groupBoxPointWidget').layout().addWidget(self.point_widget)

        self.graphicsView.setScene(self.canvas)
        self.graphicsView.load_image.connect(self.canvas.load_image)
        self.graphicsView.region_selected.connect(self.canvas.select_points)
        self.graphicsView.delete_selection.connect(self.canvas.delete_selected_points)
        self.graphicsView.relabel_selection.connect(self.canvas.relabel_selected_points)
        self.graphicsView.toggle_points.connect(self.point_widget.checkBoxDisplayPoints.toggle)

        self.graphicsView.add_point.connect(self.canvas.add_point)
        self.canvas.image_loaded.connect(self.graphicsView.image_loaded)

        # Image data fields
        self.canvas.image_loaded.connect(self.display_coordinates)
        self.canvas.image_loaded.connect(self.get_custom_field_data)
        self.canvas.fields_updated.connect(self.display_custom_fields)
        self.lineEditX.textEdited.connect(self.update_coordinates)
        self.lineEditY.textEdited.connect(self.update_coordinates)

        self.pushButtonAddField.clicked.connect(self.add_field_dialog)
        self.pushButtonDeleteField.clicked.connect(self.delete_field_dialog)

    def resizeEvent(self, theEvent):
        self.graphicsView.fitInView(self.canvas.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        self.graphicsView.setSceneRect(self.canvas.itemsBoundingRect())

    # Image data field functions
    def add_field(self):
        field_def = (self.field_name.text(), self.field_type.currentText())
        if field_def in self.canvas.custom_fields['fields']:
            print('exists')
        else:
            self.canvas.add_custom_field(field_def)
            self.add_dialog.close()

    def add_field_dialog(self):
        self.field_name = QtWidgets.QLineEdit()
        self.field_type = QtWidgets.QComboBox()
        self.field_type.addItems(['line', 'box'])
        self.add_button = QtWidgets.QPushButton('Save')
        self.add_button.clicked.connect(self.add_field)
        self.add_dialog = QtWidgets.QDialog(self)
        self.add_dialog.setWindowTitle('Add Custom Field')
        self.add_dialog.setLayout(QtWidgets.QVBoxLayout())
        self.add_dialog.layout().addWidget(self.field_name)
        self.add_dialog.layout().addWidget(self.field_type)
        self.add_dialog.layout().addWidget(self.add_button)
        self.add_dialog.show()

    def delete_field(self):
        self.canvas.delete_custom_field(self.field_list.currentText())
        self.delete_dialog.close()
    
    def delete_field_dialog(self):
        self.field_list = QtWidgets.QComboBox()
        self.field_list.addItems([x[0] for x in self.canvas.custom_fields['fields']])
        self.delete_button = QtWidgets.QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete_field)
        self.delete_dialog = QtWidgets.QDialog(self)
        self.delete_dialog.setWindowTitle('Add Custom Field')
        self.delete_dialog.setLayout(QtWidgets.QVBoxLayout())
        self.delete_dialog.layout().addWidget(self.field_list)
        self.delete_dialog.layout().addWidget(self.delete_button)
        self.delete_dialog.show()

    def display_coordinates(self, directory, image):
        if image in self.canvas.coordinates:
            self.lineEditX.setText(self.canvas.coordinates[image]['x'])
            self.lineEditY.setText(self.canvas.coordinates[image]['y'])
        else:
            self.lineEditX.setText('')
            self.lineEditY.setText('')

    def display_custom_fields(self, fields):

        def build(item):
            container = QtWidgets.QGroupBox(item[0], self)
            container.setObjectName(item[0])
            container.setLayout(QtWidgets.QVBoxLayout())
            if item[1].lower() == 'line':
                edit = LineText(container)
            else:
                edit = BoxText(container)
            edit.update.connect(self.canvas.save_custom_field_data)
            self.load_custom_data.connect(edit.load_data)
            container.layout().addWidget(edit)
            return container

        custom_fields = self.findChild(QtWidgets.QFrame, 'frameCustomFields')
        if custom_fields.layout() is None:
            custom_fields.setLayout(QtWidgets.QVBoxLayout())
        else:
            layout = custom_fields.layout()
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        for item in fields:
            widget = build(item)
            custom_fields.layout().addWidget(widget)
        v = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        custom_fields.layout().addItem(v)
        self.get_custom_field_data()

    def get_custom_field_data(self):
        self.load_custom_data.emit(self.canvas.get_custom_field_data())

    def update_coordinates(self, text):
        x = self.lineEditX.text()
        y = self.lineEditY.text()
        self.canvas.save_coordinates(x, y)
