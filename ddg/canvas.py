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
import json
import numpy as np

from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets


class Canvas(QtWidgets.QGraphicsScene):
    image_loaded = QtCore.pyqtSignal(str, str)
    points_loaded = QtCore.pyqtSignal(str)
    fields_updated = QtCore.pyqtSignal(list)
    update_point_count = QtCore.pyqtSignal(str, str, int)

    def __init__(self):
        QtWidgets.QGraphicsScene.__init__(self)
        self.points = {}
        self.colors = {}
        self.coordinates = {}
        self.custom_fields = {'fields': [], 'data': {}}
        self.classes = []
        self.selection = []

        self.directory = ''
        self.current_image_name = None
        self.current_class_name = None

        self.qt_image = None

        self.display_point_radius = 25
        self.opacity = 0.30

        self.active_brush = QtGui.QBrush(QtCore.Qt.yellow, QtCore.Qt.SolidPattern)
        self.active_pen = QtGui.QPen(self.active_brush, 2)
        self.selected_pen = QtGui.QPen(QtGui.QBrush(QtCore.Qt.red, QtCore.Qt.SolidPattern), 1)

    def add_class(self, class_name):
        if class_name not in self.classes:
            self.classes.append(class_name)
            self.classes.sort()
            self.colors[class_name] = QtGui.QColor(QtCore.Qt.black)

    def add_custom_field(self, field_def):
        self.custom_fields['fields'].append(field_def)
        self.custom_fields['data'][field_def[0]] = {}
        self.fields_updated.emit(self.custom_fields['fields'])

    def add_point(self, point):
        if self.current_image_name is not None and self.current_class_name is not None:
            if self.current_image_name not in self.points:
                self.points[self.current_image_name] = {}
            if self.current_class_name not in self.points[self.current_image_name]:
                self.points[self.current_image_name][self.current_class_name] = []
            self.points[self.current_image_name][self.current_class_name].append(point)
            self.addEllipse(QtCore.QRectF(point.x() - ((self.display_point_radius - 1) / 2), point.y() - ((self.display_point_radius - 1) / 2), self.display_point_radius, self.display_point_radius), self.active_pen, self.active_brush)
            self.update_point_count.emit(self.current_image_name, self.current_class_name, len(self.points[self.current_image_name][self.current_class_name]))

    def clear_points(self):
        for graphic in self.items():
            if type(graphic) == QtWidgets.QGraphicsEllipseItem:
                self.removeItem(graphic)

    def delete_selected_points(self):
        if self.current_image_name is not None:
            points = self.points[self.current_image_name]
            for class_name, point in self.selection:
                points[class_name].remove(point)
                self.update_point_count.emit(self.current_image_name, class_name, len(self.points[self.current_image_name][class_name]))
            self.selection = []
            self.display_points()

    def delete_custom_field(self, field):
        self.custom_fields['data'].pop(field)
        index = -1
        for i, (field_name, _) in enumerate(self.custom_fields['fields']):
            if field_name == field:
                index = i
        if index >= 0:
            self.custom_fields['fields'].pop(index)
        self.fields_updated.emit(self.custom_fields['fields'])

    def display_points(self):
        self.clear_points()
        if self.current_image_name in self.points:
            for class_name in self.points[self.current_image_name]:
                points = self.points[self.current_image_name][class_name]
                brush = QtGui.QBrush(self.colors[class_name], QtCore.Qt.SolidPattern)
                pen = QtGui.QPen(brush, 2)
                for point in points:
                    if class_name == self.current_class_name:
                        self.addEllipse(QtCore.QRectF(point.x() - ((self.display_point_radius - 1) / 2), point.y() - ((self.display_point_radius - 1) / 2), self.display_point_radius, self.display_point_radius), self.active_pen, self.active_brush)
                    else:
                        self.addEllipse(QtCore.QRectF(point.x() - ((self.display_point_radius - 1) / 2), point.y() - ((self.display_point_radius - 1) / 2), self.display_point_radius, self.display_point_radius), pen, brush)

    def export_points(self, file_name, survey_id):
        file = open(file_name, 'w')
        output = 'survey_id,image'
        for class_name in self.classes:
            output += ',' + class_name
        output += ",x,y"
        for field_name, _ in self.custom_fields['fields']:
            output += ',{}'.format(field_name)
        output += '\n'
        file.write(output)
        for image in self.points:
            output = survey_id + ',' + image
            for class_name in self.classes:
                if class_name in self.points[image]:
                    output += ',' + str(len(self.points[image][class_name]))
                else: 
                    output += ',0'
            if image in self.coordinates:
                output += ',' + self.coordinates[image]['x']
                output += ',' + self.coordinates[image]['y']
            else:
                output += ',,'
            for field_name, _ in self.custom_fields['fields']:
                if image in self.custom_fields['data'][field_name]:
                    output += ',{}'.format(self.custom_fields['data'][field_name][image])
                else:
                    output == ','
            output += "\n"
            file.write(output)
        file.close()

    def get_custom_field_data(self):
        data = {}
        if self.current_image_name is not None:
            for field_def in self.custom_fields['fields']:
                if self.current_image_name in self.custom_fields['data'][field_def[0]]:
                    data[field_def[0]] = self.custom_fields['data'][field_def[0]][self.current_image_name]
                else:
                    data[field_def[0]] = ''
        return data

    def import_metadata(self, file_name):
        file = open(file_name, 'r')
        self.directory = os.path.split(file_name)[0]
        data = json.load(file)
        file.close()
        # Backward compat
        if 'custom_fields' in data:
            self.custom_fields = data['custom_fields']
        else:
            self.custom_fields = {'fields': [], 'data': {}}
        self.colors = data['colors']
        for class_name in data['colors']:
            self.colors[class_name] = QtGui.QColor(self.colors[class_name][0], self.colors[class_name][1], self.colors[class_name][2])
        self.classes = data['classes']
        self.fields_updated.emit(self.custom_fields['fields'])
        self.points_loaded.emit('')

    def load_image(self, in_file_name):
        Image.MAX_IMAGE_PIXELS = 1000000000
        file_name = in_file_name
        if type(file_name) == QtCore.QUrl:
            file_name = in_file_name.toLocalFile()

        if self.directory == '':
            self.directory = os.path.split(file_name)[0]

        if self.directory == os.path.split(file_name)[0]:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.selection = []
            self.clear()
            self.current_image_name = os.path.split(file_name)[1]
            img = Image.open(file_name)
            array = np.array(img)
            img.close
            if array.shape[0] > 10000 or array.shape[1] > 10000:
                stride = 10
                for s in range(0, array.shape[1], stride):
                    sub = array[:,s:s+stride].copy()
                    qt_image = QtGui.QImage(sub.data, sub.shape[1], sub.shape[0], QtGui.QImage.Format_RGB888)
                    pixmap = QtGui.QPixmap.fromImage(qt_image)
                    item = self.addPixmap(pixmap)
                    item.moveBy(s, 0)
                
            else:
                # Apply basic min max stretch to the image
                array[:, :, 0] = np.interp(array[:, :, 0], (array[:, :, 0].min(), array[:, :, 0].max()), (0, 255))
                array[:, :, 1] = np.interp(array[:, :, 1], (array[:, :, 1].min(), array[:, :, 1].max()), (0, 255))
                array[:, :, 2] = np.interp(array[:, :, 2], (array[:, :, 2].min(), array[:, :, 2].max()), (0, 255))
                if array.shape[2] == 4:
                    self.qt_image = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_RGBA8888)
                else:
                    self.qt_image = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_RGB888)
                self.pixmap = QtGui.QPixmap.fromImage(self.qt_image)
                self.addPixmap(self.pixmap)
            self.image_loaded.emit(self.directory, self.current_image_name)
            self.display_points()
            QtWidgets.QApplication.restoreOverrideCursor()
        else:
            QtWidgets.QMessageBox.warning(self.parent(), 'Warning', 'Image was from outside current working directory. Load aborted.', QtWidgets.QMessageBox.Ok)

    def load_points(self, file_name):
        file = open(file_name, 'r')
        self.directory = os.path.split(file_name)[0]
        data = json.load(file)
        file.close()
        survey_id = data['metadata']['survey_id']
        # Backward compat
        if 'custom_fields' in data:
            self.custom_fields = data['custom_fields']
        else:
            self.custom_fields = {'fields': [], 'data': {}}
        self.colors = data['colors']
        self.classes = data['classes']
        self.coordinates = data['metadata']['coordinates']
        self.points = {}
        if 'points' in data:
            self.points = data['points']

        for image in self.points:
            for class_name in self.points[image]:
                for p in range(len(self.points[image][class_name])):
                    point = self.points[image][class_name][p]
                    self.points[image][class_name][p] = QtCore.QPointF(point['x'], point['y'])
        for class_name in data['colors']:
            self.colors[class_name] = QtGui.QColor(self.colors[class_name][0], self.colors[class_name][1], self.colors[class_name][2])
        self.points_loaded.emit(survey_id)
        self.fields_updated.emit(self.custom_fields['fields'])
        path = os.path.split(file_name)[0]
        path = os.path.join(path, list(self.points.keys())[0])
        self.load_image(path)

    def package_points(self, survey_id):
        count = 0
        package = {'classes': [], 'points': {}, 'colors': {}, 'metadata': {'survey_id': survey_id, 'coordinates': self.coordinates}, 'custom_fields': self.custom_fields}
        package['classes'] = self.classes
        for class_name in self.colors:
            r = self.colors[class_name].red()
            g = self.colors[class_name].green()
            b = self.colors[class_name].blue()
            package['colors'][class_name] = [r, g, b]
        for image in self.points:
            package['points'][image] = {}
            for class_name in self.points[image]:
                package['points'][image][class_name] = []
                src = self.points[image][class_name]
                dst = package['points'][image][class_name]
                for point in src:
                    p = {'x': point.x(), 'y': point.y()}
                    dst.append(p)
                    count += 1
        return (package, count)

    def relabel_selected_points(self):
        if self.current_class_name is not None:
            # for class_name, point in self.selection:
            for _, point in self.selection:
                self.add_point(point)
            self.delete_selected_points()

    def rename_class(self, old_class, new_class):
        index = self.classes.index(old_class)
        del self.classes[index]
        if new_class not in self.classes:
            self.colors[new_class] = self.colors.pop(old_class)
            self.classes.append(new_class)
            self.classes.sort()
        else:
            del self.colors[old_class]

        for image in self.points:
            if old_class in self.points[image] and new_class in self.points[image]:
                self.points[image][new_class] += self.points[image].pop(old_class)
            elif old_class in self.points[image]:
                self.points[image][new_class] = self.points[image].pop(old_class)
        self.display_points()

    def reset(self, clear_image=False):
        self.points = {}
        self.colors = {}
        self.classes = []
        self.classes = []
        self.selection = []
        self.coordinates = {}
        self.custom_fields = {'fields': [], 'data': {}}

        self.clear()
        self.current_image_name = ''
        self.current_class_name = None
        self.fields_updated.emit([])
        self.points_loaded.emit('')
        self.image_loaded.emit('', '')

    def remove_class(self, class_name):
        index = self.classes.index(class_name)
        del self.colors[class_name]
        del self.classes[index]
        for image in self.points:
            if class_name in self.points[image]:
                del self.points[image][class_name]
        self.display_points()
    
    def save_coordinates(self, x, y):
        if self.current_image_name is not None:
            if self.current_image_name not in self.coordinates:
                self.coordinates[self.current_image_name] = {'x': '', 'y': ''}
            self.coordinates[self.current_image_name]['x'] = x
            self.coordinates[self.current_image_name]['y'] = y
            self.clear_coordinates()

    def save_custom_field_data(self, field, data):
        if self.current_image_name is not None:
            if self.current_image_name not in self.custom_fields['data'][field]:
                self.custom_fields['data'][field][self.current_image_name] = ''
            self.custom_fields['data'][field][self.current_image_name] = data

    def save_points(self, file_name, survey_id):
        output, _ = self.package_points(survey_id)
        file = open(file_name, 'w')
        json.dump(output, file)
        file.close()

    def select_points(self, rect):
        self.selection = []
        self.display_points()
        current = self.points[self.current_image_name]
        for class_name in current:
            for point in current[class_name]:
                if rect.contains(point):
                    offset = ((self.display_point_radius + 6) // 2)
                    self.addEllipse(QtCore.QRectF(point.x() - offset, point.y() - offset, self.display_point_radius + 6, self.display_point_radius + 6), self.selected_pen)
                    self.selection.append((class_name, point))

    def set_current_class(self, class_index):
        if class_index is None or class_index >= len(self.classes):
            self.current_class_name = None
        else:
            self.current_class_name = self.classes[class_index]
        self.display_points()

    def set_point_radius(self, radius):
        self.display_point_radius = radius
        self.display_points()

    def toggle_points(self, display):
        if display:
            self.display_points()
            self.selection = []
        else:
            self.clear_points()
