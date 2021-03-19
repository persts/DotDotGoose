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
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from .chip_dialog import ChipDialog

# from .ui_point_widget import Ui_Pointwidget as WIDGET
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(__file__)
WIDGET, _ = uic.loadUiType(os.path.join(bundle_dir, 'point_widget.ui'))


class PointWidget(QtWidgets.QWidget, WIDGET):
    hide_custom_fields = QtCore.pyqtSignal(bool)
    class_selection_changed = QtCore.pyqtSignal()
    saving = QtCore.pyqtSignal()

    def __init__(self, canvas, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.canvas = canvas

        self.pushButtonAddClass.clicked.connect(self.add_class)
        self.pushButtonAddCategory.clicked.connect(self.add_category)
        self.pushButtonRemoveClass.clicked.connect(self.remove_class)

        self.classModel = QtGui.QStandardItemModel()
        self.classModel.setHorizontalHeaderLabels(['Name', '#', ""])
        self.classTree.setModel(self.classModel)
        self.classTree.setColumnWidth(0, 270)
        self.classTree.setColumnWidth(1, 10)
        self.classTree.setColumnWidth(2, 10)
        self.classTree.clicked.connect(self.item_clicked)
        self.classTree.doubleClicked.connect(self.rename)
        self.classTree.selectionModel().selectionChanged.connect(self.selection_changed)
        self.fill_default_categories()
        self.tree_expanded = {} # list of the expanded items in the model

        self.checkBoxDisplayPoints.toggled.connect(self.display_points)
        self.checkBoxDisplayGrid.toggled.connect(self.display_grid)
        self.canvas.image_loaded.connect(self.image_loaded)
        self.canvas.update_point_count.connect(self.update_point_count)
        self.canvas.points_loaded.connect(self.points_loaded)
        self.canvas.points_updated.connect(self.display_classes)

        # model for pictures
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Imagename', 'Total Count'])
        self.current_model_index = QtCore.QModelIndex()
        self.treeView.setModel(self.model)
        self.treeView.setColumnWidth(0, 250)
        self.treeView.setColumnWidth(1, 5)
        self.reset_model()
        self.treeView.doubleClicked.connect(self.select_model_item)

        self.previous_file_name = None  # used for quick save

        self.spinBoxPointRadius.valueChanged.connect(self.canvas.set_point_radius)
        self.spinBoxGrid.valueChanged.connect(self.canvas.set_grid_size)

        icon = QtGui.QPixmap(20, 20)
        icon.fill(QtCore.Qt.yellow)
        self.labelPointColor.setPixmap(icon)
        self.labelPointColor.mousePressEvent = self.change_active_point_color
        icon = QtGui.QPixmap(20, 20)
        icon.fill(QtCore.Qt.white)
        self.labelGridColor.setPixmap(icon)
        self.labelGridColor.mousePressEvent = self.change_grid_color

        self.checkBoxImageFields.clicked.connect(self.hide_custom_fields.emit)

    def fill_default_categories(self):
        root = self.classModel.invisibleRootItem()
        for c in self.canvas.categories:
            key, value, color_item = self._get_default_category(c)
            root.appendRow([key, value, color_item])

    def add_category(self):
        name, ok = QtWidgets.QInputDialog.getText(self, 'New Class', 'Class Name')
        if ok:
            if name in self.canvas.categories:
                dialog = QtWidgets.QMessageBox.question(self, "Choose different name", "Name "+ name + " already taken", QtWidgets.QMessageBox.Ok)
                return
            key, value, color_item = self._get_default_category(name)
            self.canvas.add_category(name)
            self.classModel.invisibleRootItem().appendRow([key, value, color_item])

    def add_class(self):
        class_name, ok = QtWidgets.QInputDialog.getText(self, 'New Class', 'Class Name')
        if ok:
            if class_name in self.canvas.classes or class_name in self.canvas.categories:
                dialog = QtWidgets.QMessageBox.question(self, "Choose different name", "Name "+ class_name + " already taken", QtWidgets.QMessageBox.Ok)
                return
            # get current selection:
            if self.canvas.current_selection is not None:
                name = self.canvas.current_selection.data(0)
                if name not in self.canvas.categories: # current selection is not a category
                    category_item = self.canvas.current_selection.parent()
                else: # selection is a category
                    category_item = self.canvas.current_selection
                category_name = category_item.data(0)
                category_index = category_item.index()
                self.canvas.add_class(category_name, class_name)
                key, value, color_item = self._get_default_class(class_name)
                if self.canvas.current_class_name is not None: # toggle previous selection
                    item = self.get_item_from_name(self.canvas.current_class_name)
                    font = item.font()
                    font.setBold(False)
                    key.setFont(font)
                # self.canvas.set_current_class(name)
                # font = key.font()
                # font.setBold(True)
                # key.setFont(font)
                self.classModel.itemFromIndex(category_index).appendRow([key, value, color_item])

    def change_active_point_color(self, event):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.set_active_point_color(color)

    def change_grid_color(self, event):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.set_grid_color(color)

    def display_classes(self):
        for i in range(self.classModel.rowCount()):
            item = self.classModel.item(i)
            self.tree_expanded[item.data(0)] = self.classTree.isExpanded(self.classModel.index(i,0))
        self.reset_class_model()
        root = self.classModel.invisibleRootItem()
        for category in self.canvas._categories:
            classes = self.canvas.data[category]
            total_count = 0
            category_item, category_count_item, _ = self._get_default_category(category)
            if len(classes) != 0:
                for class_name in classes:
                    class_item, class_count_item, class_color_item = self._get_default_class(class_name)
                    count = 0
                    for image in self.canvas.points.keys():
                        count += len(self.canvas.points[image].get(class_name, []))
                    class_count_item.setData(str(count), QtCore.Qt.EditRole)
                    total_count += count
                    category_item.appendRow([class_item, class_count_item, class_color_item])
            category_count_item.setData(str(total_count), QtCore.Qt.EditRole)
            root.appendRow([category_item, category_count_item, QtGui.QStandardItem("")])
        for row in range(self.classModel.rowCount()):
                index = self.classModel.index(row, 0)
                item = self.classModel.itemFromIndex(index)
                self.classTree.setExpanded(index, self.tree_expanded[item.data(0)])

    def display_count_tree(self):
        self.reset_model()
        for image in self.canvas.points:
            image_item = QtGui.QStandardItem(image)
            image_item.setEditable(False)
            count = 0
            for classes, points in self.canvas.points[image].items():
                count += len(points)
            count_item = QtGui.QStandardItem(str(count))
            count_item.setEditable(False)
            if image == self.canvas.current_image_name:
                font = image_item.font()
                font.setBold(True)
                image_item.setFont(font)
                self.current_model_index = image_item.index()
            self.model.appendRow([image_item, count_item])
        self.treeView.scrollTo(self.current_model_index)

    def display_grid(self, display):
        self.canvas.toggle_grid(display=display)

    def display_points(self, display):
        self.canvas.toggle_points(display=display)

    def export_counts(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Export Count Summary', os.path.join(self.canvas.directory, 'counts.csv'), 'Excel Sheet (*.csv)')
        if file_name[0] != '':
            self.canvas.export_counts(file_name[0], self.lineEditSurveyId.text())

    def export_points(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Export Points', os.path.join(self.canvas.directory, 'points.csv'), 'Text CSV (*.csv)')
        if file_name[0] != '':
            self.canvas.export_points(file_name[0], self.lineEditSurveyId.text())
    
    def export_details(self):
        self.chip_dialog = ChipDialog(self.canvas.classes, self.canvas.points, self.canvas.directory, self.lineEditSurveyId.text())
        self.chip_dialog.show()
    
    def get_item_from_name(self, name):
        if name in self.canvas.categories:
            return self.classModel.findItems(name)[0]
        elif name in self.canvas.classes:
            category_name = self.canvas.get_category_from_class(name)
            category_item = self.classModel.findItems(category_name)[0]
            index = self.canvas.data[category_name].index(name)
            return category_item.child(index, 0)

    def _get_default_category(self, name):
        key = QtGui.QStandardItem(name)
        # key.setCheckable(True) # to be implemented for export and visibility functionality
        key.setSelectable(True)
        key.setEditable(False)
        key.setTextAlignment(QtCore.Qt.AlignLeft)
        value = QtGui.QStandardItem("0")
        value.setEditable(False)
        color_item = QtGui.QStandardItem("")
        return key, value, color_item

    def _get_default_class(self, class_name):
        key = QtGui.QStandardItem(class_name)
        # key.setCheckable(True) # to be implemented for export and visibility functionality
        value = QtGui.QStandardItem("0")
        value.setEditable(False)
        color_item = QtGui.QStandardItem()
        icon = QtGui.QPixmap(20, 20)
        icon.fill(self.canvas.colors[class_name])
        color_item.setData(icon, QtCore.Qt.DecorationRole)
        color_item.setEditable(False)
        return key, value, color_item

    def item_clicked(self, index):
        if index.column() == 2:
            color = QtWidgets.QColorDialog.getColor()
            if color.isValid():
                category_item = index.parent()
                name = category_item.child(index.row(), 0).data(0)
                self.canvas.colors[name] = color
                icon = QtGui.QPixmap(20, 20)
                icon.fill(color)
                self.classModel.itemFromIndex(index).setData(icon, QtCore.Qt.DecorationRole)
                self.canvas.display_points()

    def image_loaded(self, directory, file_name):
        # self.classTree.selectionModel().clear()
        self.display_count_tree()

    def load(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Points File', self.canvas.directory, 'Point Files (*.pnt)')
        if file_name[0] != '':
            self.previous_file_name = file_name[0]
            self.canvas.load_points(file_name[0])

    def next(self):
        # to be implemented later
        return
        if self.canvas.current_class_name:
            item = self.get_item_from_name(self.canvas.current_class_name)
            font = item.font()
            font.setBold(False)
            item.setFont(font)

        if self.canvas.next_class_name:
            item = self.get_item_from_name(self.canvas.next_class_name)
            self.canvas.set_current_class(self.canvas.next_class_name)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            for i in range(self.classModel.rowCount()):
                item = self.classModel.item(i)
                for j in range(item.rowCount()):
                    if self.canvas.next_class_name == item.child(j,0).data(0):
                        index = self.classModel.index(j, 0, item.index())
                        self.classTree.selectionModel().clearSelection()
                        self.classTree.selectionModel().select(index, QtCore.QItemSelectionModel.Rows)
        self.update_closest_class_names()

    def points_loaded(self, survey_id):
        self.lineEditSurveyId.setText(survey_id)
        self.display_classes()
        self.update_ui_settings()

    def previous(self):
        # to be implemented later
        return
        if self.canvas.current_class_name:
            item = self.get_item_from_name(self.canvas.current_class_name)
            font = item.font()
            font.setBold(False)
            item.setFont(font)
            
        if self.canvas.previous_class_name:
            item = self.get_item_from_name(self.canvas.previous_class_name)
            self.canvas.set_current_class(self.canvas.previous_class_name)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            for i in range(self.classModel.rowCount()):
                item = self.classModel.item(i)
                for j in range(item.rowCount()):
                    if self.canvas.next_class_name == item.child(j,0).data(0):
                        index = self.classModel.index(j, 0, item.index())
                        # self.classTree.selectionModel().clearSelection()
                        # self.classTree.selectionModel().select(index, QtCore.QItemSelectionModel.Rows)
                        self.classTree.selectionModel().emitSelectionChanged()
        self.update_closest_class_names()

    def rename(self, index):
        column = index.column()
        row = index.row()
        class_name, ok = QtWidgets.QInputDialog.getText(self, 'New name', 'New Name')
        if class_name in self.canvas.classes or class_name in self.canvas.categories:
            dialog = QtWidgets.QMessageBox.question(self, "Choose different name", "Name "+ class_name + " already taken", QtWidgets.QMessageBox.Ok)
            return
        if column == 0 and class_name != "":
            is_expanded = self.classTree.isExpanded(index)
            old = index.data(0)
            new = class_name
            if old != new:
                self.classTree.selectionModel().clear()
                if old in self.canvas.classes:
                    self.canvas.rename_class(old, new)
                elif old in self.canvas.categories:
                    self.canvas.rename_category(old, new)
                for row in range(self.classModel.rowCount()):
                    ind = self.classModel.index(row, 0)
                    item = self.classModel.itemFromIndex(ind)
                    self.tree_expanded[item.data(0)] = self.classTree.isExpanded(ind)
                self.tree_expanded[new] = self.classTree.isExpanded(index)
                self.display_classes()
                # self.display_count_tree()

    def reset_class_model(self):
        self.classTree.reset()
        self.classModel.clear()
        self.classModel.setColumnCount(3)
        self.classModel.setHorizontalHeaderLabels(['Name', '#', ""])
        self.classTree.setColumnWidth(0, 270)
        self.classTree.setColumnWidth(1, 10)
        self.classTree.setColumnWidth(2, 10)

    def reset_model(self):
        self.current_model_index = QtCore.QModelIndex()
        self.model.clear()
        self.model.setColumnCount(2)
        self.model.setHeaderData(0, QtCore.Qt.Horizontal, 'Image')
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, 'Count')
        # self.treeView.setExpandsOnDoubleClick(False)
        # self.treeView.header().setStretchLastSection(False)
        # self.treeView.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        # self.treeView.setTextElideMode(QtCore.Qt.ElideMiddle)

    def remove_class(self):
        indexes = self.classTree.selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            item = index.model().itemFromIndex(index)
            name = item.data(0)
            msgBox = QtWidgets.QMessageBox()
            msgBox.setWindowTitle('Warning')
            msgBox.setText('You are about to remove class/category [{}] '.format(name))
            msgBox.setInformativeText('Do you want to continue?')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            response = msgBox.exec()
            if response == QtWidgets.QMessageBox.Ok:
                if name in self.canvas.categories:
                    if item.rowCount() == 0:
                        self.classModel.removeRow(item.row())
                    else:
                        self.classModel.removeRows(item.row(), item.rowCount())
                    self.canvas.remove_category(name)
                else:
                    category_item = item.parent()
                    category_item.removeRow(item.row())
                    self.canvas.remove_class(name)
                self.tree_expanded = {}
                for row in range(self.classModel.rowCount()):
                    ind = self.classModel.index(row, 0)
                    item = self.classModel.itemFromIndex(ind)
                    self.tree_expanded[item.data(0)] = self.classTree.isExpanded(ind)
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
                QtWidgets.QMessageBox.warning(self.parent(), 'ERROR', 'You are attempting to save the pnt file outside of the working directory. Operation canceled. POINT DATA NOT SAVED.', QtWidgets.QMessageBox.Ok)
            else:
                if self.canvas.save_points(file_name[0], self.lineEditSurveyId.text()) is False:
                    msg_box = QtWidgets.QMessageBox()
                    msg_box.setWindowTitle('ERROR')
                    msg_box.setText('Save Failed!')
                    msg_box.setInformativeText('It appears you cannot save your pnt file in the working directory, possibly due to permissions.\n\nEither change the permissions on the folder or click the SAVE button and select another location outside of the working directory. Remember to copy of the pnt file back into the current working directory. ')
                    msg_box.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Cancel)
                    msg_box.setDefaultButton(QtWidgets.QMessageBox.Save)
                    response = msg_box.exec()
                    if response == QtWidgets.QMessageBox.Save:
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
            index = selected.indexes()[0]
            item = self.classModel.itemFromIndex(index)
            self.canvas.current_selection = item
            name = item.data(0)
            # print("Selected: ", name, index.row(), index.column())
            categories = list(self.canvas.categories)
            if name in categories:
                self.canvas.set_current_category(name)
                self.canvas.set_current_class(None)
            else:
                # also automatically sets corrresponding category
                self.canvas.set_current_class(name)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            if len(deselected.indexes()) > 0:
                item = self.classModel.itemFromIndex(deselected.indexes()[0])
                font = item.font()
                font.setBold(False)
                item.setFont(font)
            # self.update_closest_class_names() to be implemented later
        else:
            self.canvas.set_current_class(None)
        self.class_selection_changed.emit()

    def set_active_point_color(self, color):
        icon = QtGui.QPixmap(20, 20)
        icon.fill(color)
        self.labelPointColor.setPixmap(icon)
        self.canvas.set_point_color(color)

    def set_active_class(self, row):
        if row < self.classTree.rowCount():
            self.classTree.selectRow(row)

    def set_grid_color(self, color):
        icon = QtGui.QPixmap(20, 20)
        icon.fill(color)
        self.labelGridColor.setPixmap(icon)
        self.canvas.set_grid_color(color)

    def update_point_count(self, image_name, class_name, count):
        img_items = self.model.findItems(image_name)
        if len(img_items) == 0:
            self.display_count_tree()
        else:
            class_item = self.canvas.current_selection
            category_item = class_item.parent()
            row = class_item.row()
            category_item.child(row, 1).setData(str(count), QtCore.Qt.EditRole)
            total_count = 0
            for i in range(category_item.rowCount()):
                total_count += int(category_item.child(i, 1).data(0))
            self.classModel.itemFromIndex(self.classModel.index(category_item.row(), 1)).setData(str(total_count), QtCore.Qt.EditRole)
            total_count = 0
            for i in range(self.classModel.rowCount()):
                index = self.classModel.index(i, 1)
                item = self.classModel.itemFromIndex(index)
                total_count += int(item.data(0))
            img_item = img_items[0]
            row = img_item.row()
            self.display_count_tree()

    def update_ui_settings(self):
        ui = self.canvas.ui
        color = QtGui.QColor(ui['point']['color'][0], ui['point']['color'][1], ui['point']['color'][2])
        self.set_active_point_color(color)
        self.spinBoxPointRadius.setValue(ui['point']['radius'])
        color = QtGui.QColor(ui['grid']['color'][0], ui['grid']['color'][1], ui['grid']['color'][2])
        self.set_grid_color(color)
        self.spinBoxGrid.setValue(ui['grid']['size'])

    def update_closest_class_names(self):
        from itertools import cycle
        
        current_class_name = self.canvas.current_class_name
        current_category_name = self.canvas.current_category_name

        if len(self.canvas.classes) < 2:
            previous_name = current_class_name
            next_name = current_class_name
            return

        if current_category_name is None:
            return
        
        category_index = self.canvas.categories.index(current_category_name)
        categories = cycle(self.canvas.categories)

        if current_category_name is None:
            classes = self.canvas.data[current_category_name]
            i = category_index
            while len(classes) == 0:
                category = categories[i]
                classes = self.canvas.data[category]
                i = i + 1
            next_name = classes[0]
            i = category_index - 1
            while len(classes) == 0:
                category = categories[i]
                classes = self.canvas.data[category]
                i = i - 1
            previous_name = classes[0]
        else:
            class_index = self.canvas.classes.index(current_class_name)
            next_name = self.canvas.classes[(class_index + 1) % len(self.canvas.classes)]
            previous_name = self.canvas.classes[class_index - 1]
                
        self.canvas.previous_class_name = previous_name
        self.canvas.next_class_name = next_name
        print("Closest:", self.canvas.previous_class_name, self.canvas.current_class_name, self.canvas.next_class_name)
