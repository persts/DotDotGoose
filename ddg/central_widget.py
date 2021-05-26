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
from itertools import cycle
from PyQt5 import QtCore, QtWidgets, QtGui

from ddg import Canvas
from ddg.canvas import Scale, completion
from ddg import PointWidget
from .ui.central_widget_ui import Ui_CentralWidget as CLASS_DIALOG

class ListView(QtWidgets.QListView):
    def event(self, e):
        print(e)
        return super().event(e)


class LineEdit(QtWidgets.QLineEdit):
    copy_all_signal = QtCore.pyqtSignal()
    paste_all_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None, available_actions=["Copy", "Copy All Details", "Paste", "Paste All Details", "Convert To Uppercase"]):
        super().__init__(parent)
        self.available_actions = available_actions
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.createMenu)

    def createMenu(self, position):
        self.menu = QtWidgets.QMenu()
        copy_one = self.menu.addAction("Copy (CTRL+C)")
        paste_one = self.menu.addAction("Paste (CTRL+V)")
        cut_one = self.menu.addAction("Cut (CTRL+X)")
        self.menu.addSeparator()
        copy_all = self.menu.addAction("Copy All Details")
        paste_all = self.menu.addAction("Paste All Details")
        self.menu.addSeparator()
        convert_to_uppercase = self.menu.addAction("Convert to Uppercase")
        convert_to_lowercase = self.menu.addAction("Convert to Lowercase")
        if "Copy All Details" not in self.available_actions:
            copy_all.setEnabled(False)
        if "Paste All Details" not in self.available_actions:
            paste_all.setEnabled(False)
        if "Convert To Uppercase" not in self.available_actions:
            convert_to_uppercase.setEnabled(False)
            convert_to_lowercase.setEnabled(False)
        action = self.menu.exec_(self.mapToGlobal(position))
        if action is None:
            return
        if action == copy_one:
            self.copy_one()
        elif action == paste_one:
            self.paste_one()
        elif action == cut_one:
            self.cut_one()
        elif action == copy_all:
            self.copy_all_signal.emit()
        elif action == paste_all:
            self.paste_all_signal.emit()
        elif action == convert_to_uppercase:
            self.convert_to_uppercase()
        elif action == convert_to_lowercase:
            self.convert_to_lowercase()

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        key = a0.key()
        if key == QtCore.Qt.Key_Escape:
            self.clearFocus()
        else:
            return super().keyPressEvent(a0)

    def copy_one(self):
        clipboard = QtWidgets.QApplication.clipboard()
        if len(self.selectedText()) > 0:
            text = self.selectedText()
        else:
            text = self.text()
        clipboard.setText(text)

    def convert_to_uppercase(self):
        text = self.text().upper()
        self.setText(text)
        self.textEdited.emit(text)

    def convert_to_lowercase(self):
        text = self.text().lower()
        self.setText(text)
        self.textEdited.emit(text)

    def cut_one(self):
        clipboard = QtWidgets.QApplication.clipboard()
        if len(self.selectedText()) > 0:
            text = self.selectedText()
        else:
            text = self.text()
        clipboard.setText(text)
        text = self.text().replace(text, "")
        self.setText(text)
        self.textEdited.emit(text)

    def paste_one(self):
        clipboard = QtWidgets.QApplication.clipboard()
        text = self.text()
        n = len(text)
        ctext = clipboard.text()
        if len(self.selectedText()) > 0:
            text = text.replace(self.selectedText(), ctext).strip()
        else:
            pos = min(self.cursorPosition(), n)
            text = text[:pos] + ctext + text[pos:]
        self.setText(text)
        self.textEdited.emit(text)


class CentralWidget(QtWidgets.QDialog, CLASS_DIALOG):

    load_custom_data = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        _translate = QtCore.QCoreApplication.translate
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

        self.graphicsView.setScene(self.canvas)
        self.graphicsView.drop_complete.connect(self.canvas.load)
        self.graphicsView.region_selected.connect(self.canvas.select_points)
        self.graphicsView.delete_selection.connect(self.canvas.delete_selected_points)
        self.graphicsView.clear_selection.connect(self.canvas.clear_selection)
        self.graphicsView.relabel_selection.connect(self.canvas.relabel_selected_points)
        self.graphicsView.measure_area.connect(self.canvas.measure_area)
        self.graphicsView.toggle_points.connect(self.point_widget.checkBoxDisplayPoints.toggle)
        self.graphicsView.toggle_grid.connect(self.point_widget.checkBoxDisplayGrid.toggle)
        self.graphicsView.scale_selected.connect(self.set_scale)
        self.graphicsView.select_class.connect(self.point_widget.select_tree_item_from_name)
        self.graphicsView.add_class.connect(lambda: self.point_widget.add_class(askname=False))

        self.graphicsView.add_point.connect(self.canvas.add_point)
        self.graphicsView.display_pointer_coordinates.connect(self.display_pointer_coordinates)
        self.graphicsView.find_point.connect(self.find_point)
        self.canvas.image_loaded.connect(self.graphicsView.image_loaded)
        self.canvas.directory_set.connect(self.display_working_directory)

        # Image data fields
        self.canvas.image_loaded.connect(self.display_coordinates)
        self.canvas.image_loaded.connect(self.display_attributes)
        self.canvas.fields_updated.connect(self.display_attributes)

        self.dataLineEditsNames = ["lineEditX", "lineEditY"]
        pcbAttr = ["Length", "Width"]

        self.attributeLineEditsNames = ["lineEdit_description", "lineEdit_marking", 
                     "lineEdit_partnumber", "lineEdit_manufacturer", "lineEdit_package", 
                     "lineEdit_length", "lineEdit_width", "lineEdit_height", "lineEdit_pincount"]

        attributes = ["Description", "Marking", "Partnumber", "Manufacturer", "Package", "Length",
                      "Width", "Height", "IO/Pin Count"]

        for i, k in enumerate(self.dataLineEditsNames):
            box = self.groupBoxImageData
            layout = self.gridLayout_2
            lineEdit = LineEdit(box, available_actions=["Copy", "Paste"])
            lineEdit.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            lineEdit.setAcceptDrops(False)
            lineEdit.setObjectName(k)
            lineEdit.textEdited.connect(self.update_coordinates)
            lineEdit.setDisabled(True)
            lineEdit.returnPressed.connect(self.cycle_edits)
            layout.addWidget(lineEdit, i, 1, 1, 1)

            label = QtWidgets.QLabel(box)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(label.sizePolicy().hasHeightForWidth())
            label.setSizePolicy(sizePolicy)
            label.setText(_translate("CentralWidget", pcbAttr[i]))
            layout.addWidget(label, i, 0, 1, 1)
            setattr(self, k, lineEdit)

        self.lineEdit_attributes = {}
        for i, k in enumerate(self.attributeLineEditsNames):
            box = self.groupBoxCustomFields
            layout = self.gridLayout
            lineEdit = LineEdit(box)
            lineEdit.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            lineEdit.setAcceptDrops(False)
            lineEdit.setObjectName(k)
            lineEdit.textEdited.connect(self.update_attributes)
            lineEdit.returnPressed.connect(self.cycle_edits)
            lineEdit.setDisabled(True)
            lineEdit.copy_all_signal.connect(self.copy_all_attributes)
            lineEdit.paste_all_signal.connect(self.paste_all_attributes)
            layout.addWidget(lineEdit, i, 1, 1, 1)

            label = QtWidgets.QLabel(box)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(label.sizePolicy().hasHeightForWidth())
            label.setSizePolicy(sizePolicy)
            label.setText(_translate("CentralWidget", attributes[i]))
            layout.addWidget(label, i, 0, 1, 1)

            self.lineEdit_attributes[attributes[i]] = lineEdit
            setattr(self, k, lineEdit)
            setattr(self, k.replace("lineEdit", "label"), label)

        self.lineEdits = self.dataLineEditsNames.copy()
        self.lineEdits.extend(self.attributeLineEditsNames)

        package_completer = QtWidgets.QCompleter(completion.packages)
        package_completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.lineEdit_package.setCompleter(package_completer)
        package_completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

        manufacturer_completer = QtWidgets.QCompleter(completion.manufacturers)
        manufacturer_completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.lineEdit_manufacturer.setCompleter(manufacturer_completer)
        manufacturer_completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

        self.pushButtonFolder.clicked.connect(self.select_folder)
        self.pushButtonZoomOut.clicked.connect(self.graphicsView.zoom_out)
        self.pushButtonZoomIn.clicked.connect(self.graphicsView.zoom_in)

        self.quick_save_frame = QtWidgets.QFrame(self.graphicsView)
        self.quick_save_frame.setStyleSheet("QFrame { background: #4caf50;color: #FFF;font-weight: bold}")
        self.quick_save_frame.setLayout(QtWidgets.QHBoxLayout())
        self.quick_save_frame.layout().addWidget(QtWidgets.QLabel('Saving...'))
        self.quick_save_frame.setGeometry(3, 3, 100, 35)
        self.quick_save_frame.hide()
        
        self.toolBar = QtWidgets.QToolBar()
        self.toolLayout.addWidget(self.toolBar)
        self.pointsToolButton = QtWidgets.QToolButton()
        self.pointsToolButton.setText("Count")
        self.pointsToolButton.setCheckable(True)
        self.pointsToolButton.setChecked(True)
        self.pointsToolButton.setAutoExclusive(True)
        self.toolBar.addWidget(self.pointsToolButton)
        self.rectsToolButton = QtWidgets.QToolButton()
        self.rectsToolButton.setText("Measure")
        self.rectsToolButton.setCheckable(True)
        self.rectsToolButton.setChecked(False)
        self.rectsToolButton.setAutoExclusive(True)
        self.toolBar.addWidget(self.rectsToolButton)

    def copy_all_attributes(self):
        from os import linesep
        clipboard = QtWidgets.QApplication.clipboard()
        text = ""
        for attr_name, lineEdit in self.lineEdit_attributes.items():
            text = text + lineEdit.text() + linesep
        clipboard.setText(text.strip(linesep))

    def paste_all_attributes(self):
        from os import linesep
        clipboard = QtWidgets.QApplication.clipboard()
        text = clipboard.text()
        if linesep in text:
            text = text.split(linesep)
        elif "\n" in text:
            text = text.split("\n")
        if text[-1] == "\n" or text[-1] == linesep:
            text = text[:-1]
        attributes = list(self.lineEdit_attributes.keys())
        for i, t in enumerate(text):
            if i == len(attributes):
                break
            self.lineEdit_attributes[attributes[i]].setText(text[i])

    def cycle_edits(self):
        cycled = cycle(self.lineEdits)
        for k in cycled:
            lineEdit = getattr(self, k)
            if lineEdit.hasFocus():
                lineEdit.clearFocus()
                nextLineEdit = getattr(self, next(cycled))
                nextLineEdit.setFocus()
                break

    def display_pointer_coordinates(self, point):
        img = self.canvas.current_image_name
        image_scale = self.canvas.image_scale.get(img, Scale())
        scale = image_scale.scale
        left = image_scale.left
        top = image_scale.top
        unit = image_scale.unit
        text = "{:.1f}, {:.1f} {}".format(int(point.x())*scale - left, int(point.y())*scale - top, unit)
        self.posLabel.setText(text)

    def display_coordinates(self, directory, image):
        if self.canvas.current_image_name is None:
            self.lineEditX.setDisabled(True)
            self.lineEditY.setDisabled(True)
        else:
            self.lineEditX.setDisabled(False)
            self.lineEditY.setDisabled(False)
        if image in self.canvas.coordinates:
            self.lineEditX.setText(self.canvas.coordinates[image]['x'])
            self.lineEditY.setText(self.canvas.coordinates[image]['y'])
        else:
            self.lineEditX.setText('')
            self.lineEditY.setText('')

    def display_attributes(self):
        if self.canvas.current_class_name is None or self.canvas.current_image_name is None:
            for _, lineEdit in self.lineEdit_attributes.items():
                lineEdit.setText("")
                lineEdit.setDisabled(True)
        else:
            for k, lineEdit in self.lineEdit_attributes.items():
                lineEdit.setDisabled(False)
                value = self.canvas.class_attributes[self.canvas.current_class_name][k]
                if k == "Packages":
                    if value not in completion.packages:
                        completion.update(packages=[value])
                        self.lineEdit_package.setCompleter(QtWidgets.QCompleter(completion.packages))
                elif k == "Manufacturer":
                    if value not in completion.manufacturers:
                        completion.update(manufacturers=[value])
                        self.lineEdit_manufacturer.setCompleter(QtWidgets.QCompleter(completion.manufacturers))
                lineEdit.setText(value)
                
    def display_working_directory(self, directory):
        self.labelWorkingDirectory.setText(directory)

    def display_quick_save(self):
        self.quick_save_frame.show()
        QtCore.QTimer.singleShot(500, self.quick_save_frame.hide)

    def find_point(self, point):
        self.graphicsView.hovered_name = None
        if self.canvas.current_image_name is None:
            return
        item = self.canvas.itemAt(point, QtGui.QTransform())
        if item is None or not isinstance(item, QtWidgets.QGraphicsEllipseItem):
            return
        classes = self.canvas.points[self.canvas.current_image_name]
        if len(classes) == 0:
            return
        for c, points in classes.items():
            for p in points:
                if item.contains(p):
                    self.graphicsView.hovered_name = c
                    break

    def hide_custom_fields(self, hide):
        if hide is True:
            self.frameCustomField.hide()
        else:
            self.frameCustomField.show()

    def resizeEvent(self, theEvent):
        self.graphicsView.resize_image()

    def set_scale(self, rect):
        mm, ok = QtWidgets.QInputDialog.getInt(self, 'Set scale', 'Enter Length (x-axis) in mm')
        if ok:
            self.canvas.set_scale(mm, rect)

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