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
from PyQt6 import QtCore, QtGui, QtWidgets, uic

from .chip_dialog import ChipDialog

# from .ui_point_widget import Ui_Pointwidget as WIDGET
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(__file__)
WIDGET, _ = uic.loadUiType(os.path.join(bundle_dir, 'point_widget.ui'))


class PointWidget(QtWidgets.QWidget, WIDGET):
    hide_custom_fields = QtCore.pyqtSignal(bool)
    saving = QtCore.pyqtSignal()

    def __init__(self, canvas, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.canvas = canvas

        self.pushButtonAddClass.clicked.connect(self.add_class)
        self.pushButtonRemoveClass.clicked.connect(self.remove_class)
        self.pushButtonImport.clicked.connect(self.import_metadata)
        self.pushButtonSave.clicked.connect(self.save)
        self.pushButtonLoadPoints.clicked.connect(self.load)
        self.pushButtonReset.clicked.connect(self.reset)
        self.pushButtonExport.clicked.connect(self.export)

        self.pushButtonExport.setIcon(QtGui.QIcon('icons:export.svg'))
        self.pushButtonReset.setIcon(QtGui.QIcon('icons:reset.svg'))
        self.pushButtonImport.setIcon(QtGui.QIcon('icons:import.svg'))
        self.pushButtonSave.setIcon(QtGui.QIcon('icons:save.svg'))
        self.pushButtonLoadPoints.setIcon(QtGui.QIcon('icons:load.svg'))
        self.pushButtonRemoveClass.setIcon(QtGui.QIcon('icons:delete.svg'))
        self.pushButtonAddClass.setIcon(QtGui.QIcon('icons:add.svg'))

        self.tableWidgetClasses.verticalHeader().setVisible(False)
        self.tableWidgetClasses.horizontalHeader().setMinimumSectionSize(1)
        self.tableWidgetClasses.horizontalHeader().setStretchLastSection(False)
        self.tableWidgetClasses.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tableWidgetClasses.setColumnWidth(1, 30)
        self.tableWidgetClasses.cellClicked.connect(self.cell_clicked)
        self.tableWidgetClasses.cellChanged.connect(self.cell_changed)
        self.tableWidgetClasses.selectionModel().selectionChanged.connect(self.selection_changed)

        self.checkBoxDisplayPoints.toggled.connect(self.display_points)
        self.checkBoxDisplayGrid.toggled.connect(self.display_grid)
        self.canvas.image_loaded.connect(self.image_loaded)
        self.canvas.update_point_count.connect(self.update_point_count)
        self.canvas.points_loaded.connect(self.points_loaded)
        self.canvas.metadata_imported.connect(self.display_count_tree)

        self.model = QtGui.QStandardItemModel()
        self.current_model_index = QtCore.QModelIndex()
        self.treeView.setModel(self.model)
        self.reset_model()
        self.treeView.doubleClicked.connect(self.select_model_item)

        self.previous_file_name = None  # used for quick save

        self.spinBoxPointRadius.valueChanged.connect(self.canvas.set_point_radius)
        self.spinBoxGrid.valueChanged.connect(self.canvas.set_grid_size)

        icon = QtGui.QPixmap(20, 20)
        icon.fill(QtCore.Qt.GlobalColor.yellow)
        self.labelPointColor.setPixmap(icon)
        self.labelPointColor.mousePressEvent = self.change_active_point_color
        icon = QtGui.QPixmap(20, 20)
        icon.fill(QtCore.Qt.GlobalColor.white)
        self.labelGridColor.setPixmap(icon)
        self.labelGridColor.mousePressEvent = self.change_grid_color

        self.checkBoxImageFields.clicked.connect(self.hide_custom_fields.emit)

    def add_class(self):
        class_name, ok = QtWidgets.QInputDialog.getText(self, 'New Class', 'Class Name')
        if ok:
            self.canvas.add_class(class_name)
            self.display_classes()
            self.display_count_tree()

    def display_grid(self, display):
        self.canvas.toggle_grid(display=display)

    def display_points(self, display):
        self.canvas.toggle_points(display=display)

    def cell_changed(self, row, column):
        if column == 0:
            old_class = self.canvas.classes[row]
            new_class = self.tableWidgetClasses.item(row, column).text()
            if old_class != new_class:
                self.tableWidgetClasses.selectionModel().clear()
                self.canvas.rename_class(old_class, new_class)
                self.display_classes()
                self.display_count_tree()

    def cell_clicked(self, row, column):
        if column == 1:
            color = QtWidgets.QColorDialog.getColor()
            if color.isValid():
                self.canvas.colors[self.canvas.classes[row]] = color
                item = QtWidgets.QTableWidgetItem()
                icon = QtGui.QPixmap(20, 20)
                icon.fill(color)
                item.setData(QtCore.Qt.ItemDataRole.DecorationRole, icon)
                self.tableWidgetClasses.setItem(row, 1, item)

    def change_active_point_color(self, event):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.set_active_point_color(color)

    def change_grid_color(self, event):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.set_grid_color(color)

    def display_classes(self):
        self.tableWidgetClasses.setRowCount(len(self.canvas.classes))
        row = 0
        for class_name in self.canvas.classes:
            item = QtWidgets.QTableWidgetItem(class_name)
            self.tableWidgetClasses.setItem(row, 0, item)

            item = QtWidgets.QTableWidgetItem()
            icon = QtGui.QPixmap(20, 20)
            icon.fill(self.canvas.colors[class_name])
            item.setData(QtCore.Qt.ItemDataRole.DecorationRole, icon)
            self.tableWidgetClasses.setItem(row, 1, item)
            row += 1
        self.tableWidgetClasses.selectionModel().clear()

    def display_count_tree(self):
        self.reset_model()
        for image in self.canvas.points:
            image_item = QtGui.QStandardItem(image)
            image_item.setEditable(False)
            class_item = QtGui.QStandardItem('')
            class_item.setEditable(False)
            self.model.appendRow([image_item, class_item])
            if image == self.canvas.current_image_name:
                font = image_item.font()
                font.setBold(True)
                image_item.setFont(font)
                self.treeView.setExpanded(image_item.index(), True)
                self.current_model_index = image_item.index()

            for class_name in self.canvas.classes:
                class_item = QtGui.QStandardItem(class_name)
                class_item.setEditable(False)
                class_item.setSelectable(False)
                class_count = QtGui.QStandardItem('0')
                if class_name in self.canvas.points[image]:
                    class_count = QtGui.QStandardItem(str(len(self.canvas.points[image][class_name])))
                class_count.setEditable(False)
                class_count.setSelectable(False)
                image_item.appendRow([class_item, class_count])
        self.treeView.scrollTo(self.current_model_index)

    def export(self):
        if self.radioButtonCounts.isChecked():
            file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Export Count Summary', os.path.join(self.canvas.directory, 'counts.csv'), 'Text CSV (*.csv)')
            if file_name[0] != '':
                self.canvas.export_counts(file_name[0], self.lineEditSurveyId.text())
        elif self.radioButtonPoints.isChecked():
            file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Export Points', os.path.join(self.canvas.directory, 'points.csv'), 'Text CSV (*.csv)')
            if file_name[0] != '':
                self.canvas.export_points(file_name[0], self.lineEditSurveyId.text())
        else:
            self.chip_dialog = ChipDialog(self.canvas.classes, self.canvas.points, self.canvas.directory, self.lineEditSurveyId.text())
            self.chip_dialog.show()

    def image_loaded(self, directory, file_name):
        # self.tableWidgetClasses.selectionModel().clear()
        self.display_count_tree()

    def import_metadata(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Points File', self.canvas.directory, 'Point Files (*.pnt)')
        if file_name[0] != '':
            self.canvas.import_metadata(file_name[0])

    def load(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Points File', self.canvas.directory, 'Point Files (*.pnt)')
        if file_name[0] != '':
            self.previous_file_name = file_name[0]
            self.canvas.load_points(file_name[0])

    def next(self):
        max_index = self.model.rowCount()
        next_index = self.current_model_index.row() + 1
        if next_index < max_index:
            item = self.model.item(next_index)
            self.select_model_item(item.index())

    def points_loaded(self, survey_id):
        self.lineEditSurveyId.setText(survey_id)
        self.display_classes()
        self.update_ui_settings()

    def previous(self):
        next_index = self.current_model_index.row() - 1
        if next_index >= 0:
            item = self.model.item(next_index)
            self.select_model_item(item.index())

    def reset(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setWindowTitle('Warning')
        msgBox.setText('You are about to clear all data')
        msgBox.setInformativeText('Do you want to continue?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Cancel | QtWidgets.QMessageBox.StandardButton.Ok)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Cancel)
        response = msgBox.exec()
        if response == QtWidgets.QMessageBox.StandardButton.Ok:
            self.canvas.reset()
            self.display_classes()
            self.display_count_tree()
            self.previous_file_name = None

    def reset_model(self):
        self.current_model_index = QtCore.QModelIndex()
        self.model.clear()
        self.model.setColumnCount(2)
        self.model.setHeaderData(0, QtCore.Qt.Orientation.Horizontal, 'Image')
        self.model.setHeaderData(1, QtCore.Qt.Orientation.Horizontal, 'Count')
        self.treeView.setExpandsOnDoubleClick(False)
        self.treeView.header().setStretchLastSection(False)
        self.treeView.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.treeView.setTextElideMode(QtCore.Qt.TextElideMode.ElideMiddle)

    def remove_class(self):
        indexes = self.tableWidgetClasses.selectedIndexes()
        if len(indexes) > 0:
            class_name = self.canvas.classes[indexes[0].row()]
            msgBox = QtWidgets.QMessageBox()
            msgBox.setWindowTitle('Warning')
            msgBox.setText('You are about to remove class [{}] '.format(class_name))
            msgBox.setInformativeText('Do you want to continue?')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Cancel | QtWidgets.QMessageBox.StandardButton.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Cancel)
            response = msgBox.exec()
            if response == QtWidgets.QMessageBox.StandardButton.Ok:
                self.canvas.remove_class(class_name)
                self.display_classes()
                self.display_count_tree()

    def quick_save(self):
        if self.previous_file_name is None:
            self.save()
        else:
            self.saving.emit()
            self.canvas.save_points(self.previous_file_name, self.lineEditSurveyId.text())

    def save(self, override=False):
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Points', os.path.join(self.canvas.directory, 'untitled.pnt'), 'Point Files (*.pnt)')
        if file_name[0] != '':
            self.previous_file_name = file_name[0]
            if override is False and self.canvas.directory != os.path.split(file_name[0])[0]:
                QtWidgets.QMessageBox.warning(self.parent(), 'ERROR', 'You are attempting to save the pnt file outside of the working directory. Operation canceled. POINT DATA NOT SAVED.', QtWidgets.QMessageBox.StandardButton.Ok)
            else:
                if self.canvas.save_points(file_name[0], self.lineEditSurveyId.text()) is False:
                    msg_box = QtWidgets.QMessageBox()
                    msg_box.setWindowTitle('ERROR')
                    msg_box.setText('Save Failed!')
                    msg_box.setInformativeText('It appears you cannot save your pnt file in the working directory, possibly due to permissions.\n\nEither change the permissions on the folder or click the SAVE button and select another location outside of the working directory. Remember to copy of the pnt file back into the current working directory. ')
                    msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Save | QtWidgets.QMessageBox.StandardButton.Cancel)
                    msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Save)
                    response = msg_box.exec()
                    if response == QtWidgets.QMessageBox.StandardButton.Save:
                        self.save(True)

    def select_model_item(self, model_index):
        item = self.model.itemFromIndex(model_index)
        if item.isSelectable():
            if item.column() != 0:
                index = self.model.index(item.row(), 0)
                item = self.model.itemFromIndex(index)
            path = os.path.join(self.canvas.directory, item.text())
            self.canvas.load_image(path)

    def selection_changed(self, selected, deselected):
        if len(selected.indexes()) > 0:
            self.canvas.set_current_class(selected.indexes()[0].row())
        else:
            self.canvas.set_current_class(None)

    def set_active_point_color(self, color):
        icon = QtGui.QPixmap(20, 20)
        icon.fill(color)
        self.labelPointColor.setPixmap(icon)
        self.canvas.set_point_color(color)

    def set_active_class(self, row):
        if row < self.tableWidgetClasses.rowCount():
            self.tableWidgetClasses.selectRow(row)

    def set_grid_color(self, color):
        icon = QtGui.QPixmap(20, 20)
        icon.fill(color)
        self.labelGridColor.setPixmap(icon)
        self.canvas.set_grid_color(color)

    def update_point_count(self, image_name, class_name, class_count):
        items = self.model.findItems(image_name)
        if len(items) == 0:
            self.display_count_tree()
        else:
            items[0].child(self.canvas.classes.index(class_name), 1).setText(str(class_count))

    def update_ui_settings(self):
        ui = self.canvas.ui
        color = QtGui.QColor(ui['point']['color'][0], ui['point']['color'][1], ui['point']['color'][2])
        self.set_active_point_color(color)
        self.spinBoxPointRadius.setValue(ui['point']['radius'])
        color = QtGui.QColor(ui['grid']['color'][0], ui['grid']['color'][1], ui['grid']['color'][2])
        self.set_grid_color(color)
        self.spinBoxGrid.setValue(ui['grid']['size'])
