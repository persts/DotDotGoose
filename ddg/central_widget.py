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
        self.graphicsView.switch_class.connect(self.point_widget.set_active_class)

        self.graphicsView.add_point.connect(self.canvas.add_point)
        self.canvas.image_loaded.connect(self.graphicsView.image_loaded)
        self.canvas.directory_set.connect(self.display_working_directory)

        # Image data fields
        self.canvas.image_loaded.connect(self.display_coordinates)
        self.canvas.image_loaded.connect(self.get_custom_field_data)
        self.canvas.fields_updated.connect(self.display_custom_fields)
        self.lineEditX.textEdited.connect(self.update_coordinates)
        self.lineEditY.textEdited.connect(self.update_coordinates)

        self.pushButtonAddField.clicked.connect(self.add_field_dialog)
        self.pushButtonDeleteField.clicked.connect(self.delete_field_dialog)
        self.pushButtonFolder.clicked.connect(self.select_folder)
        self.pushButtonZoomOut.clicked.connect(self.graphicsView.zoom_out)
        self.pushButtonZoomIn.clicked.connect(self.graphicsView.zoom_in)

    def resizeEvent(self, theEvent):
        self.graphicsView.resize_image()

    # Image data field functions
    def add_field(self):
        field_def = (self.field_name.text(), self.field_type.currentText())
        field_names = [x[0] for x in self.canvas.custom_fields['fields']]
        if field_def[0] in field_names:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Field name already exists')
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
        self.add_dialog.resize(250, self.add_dialog.height())
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
        self.delete_dialog.setWindowTitle('Delete Custom Field')
        self.delete_dialog.setLayout(QtWidgets.QVBoxLayout())
        self.delete_dialog.layout().addWidget(self.field_list)
        self.delete_dialog.layout().addWidget(self.delete_button)
        self.delete_dialog.resize(250, self.delete_dialog.height())
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

    def display_working_directory(self, directory):
        self.labelWorkingDirectory.setText(directory)

    def get_custom_field_data(self):
        self.load_custom_data.emit(self.canvas.get_custom_field_data())

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
