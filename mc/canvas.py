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
import os
import json
import numpy as np

from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets


class Canvas(QtWidgets.QGraphicsScene):
    image_loaded = QtCore.pyqtSignal(str, str)
    points_loaded = QtCore.pyqtSignal()
    update_point_count = QtCore.pyqtSignal(str, str, int)

    def __init__(self):
        QtWidgets.QGraphicsScene.__init__(self)
        self.points = {}
        self.colors = {}
        self.classes = []
        self.selection = []

        self.directory = ''
        self.current_image_name = None
        self.current_class_name = None

        self.base_image = None
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
            if type(graphic) is not QtWidgets.QGraphicsPixmapItem:
                self.removeItem(graphic)

    def delete_selected_points(self):
        if self.current_image_name is not None:
            points = self.points[self.current_image_name]
            for class_name, point in self.selection:
                points[class_name].remove(point)
                self.update_point_count.emit(self.current_image_name, class_name, len(self.points[self.current_image_name][class_name]))
            self.selection = []
            self.display_points()

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

    def export_points(self, directory):
        for image in self.points:
            file = open(os.path.join(directory, image + '.csv'), 'w')
            file.write("x,y,label\n")
            for class_name in self.points[image]:
                points = self.points[image][class_name]
                for point in points:
                    file.write("{},{},{}\n".format(point.x(), point.y(), class_name))
            file.close()

    def load_image(self, in_file_name):
        file_name = in_file_name
        if type(file_name) == QtCore.QUrl:
            file_name = in_file_name.toLocalFile()

        if self.directory == '':
            self.directory = os.path.split(file_name)[0]

        if self.directory == os.path.split(file_name)[0]:
            self.selection = []
            self.clear()
            self.current_image_name = os.path.split(file_name)[1]
            self.base_image = Image.open(file_name)
            imageArray = np.array(self.base_image)
            # Apply basic min max stretch to the image
            imageArray[:, :, 0] = np.interp(imageArray[:, :, 0], (imageArray[:, :, 0].min(), imageArray[:, :, 0].max()), (0, 255))
            imageArray[:, :, 1] = np.interp(imageArray[:, :, 1], (imageArray[:, :, 1].min(), imageArray[:, :, 1].max()), (0, 255))
            imageArray[:, :, 2] = np.interp(imageArray[:, :, 2], (imageArray[:, :, 2].min(), imageArray[:, :, 2].max()), (0, 255))
            self.qt_image = QtGui.QImage(imageArray.data, imageArray.shape[1], imageArray.shape[0], QtGui.QImage.Format_RGB888)
            self.addPixmap(QtGui.QPixmap.fromImage(self.qt_image))

            self.image_loaded.emit(self.directory, self.current_image_name)
            self.display_points()
        else:
            QtWidgets.QMessageBox.warning(self.parent(), 'Warning', 'Image was from outside current working directory. Load aborted.', QtWidgets.QMessageBox.Ok)

    def load_points(self, file_name):
        file = open(file_name, 'r')
        self.directory = os.path.split(file_name)[0]
        data = json.load(file)
        file.close()
        self.colors = data['colors']
        self.classes = data['classes']
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
        self.points_loaded.emit()
        path = os.path.split(file_name)[0]
        path = os.path.join(path, list(self.points.keys())[0])
        self.load_image(path)

    def package_points(self):
        count = 0
        package = {'classes': [], 'points': {}, 'colors': {}}
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
        if clear_image:
            self.clear()
            self.current_image_name = ''
            self.current_class_name = None
        else:
            self.clear_points()

    def remove_class(self, class_name):
        index = self.classes.index(class_name)
        del self.colors[class_name]
        del self.classes[index]
        for image in self.points:
            if class_name in self.points[image]:
                del self.points[image][class_name]
        self.display_points()

    def save_points(self, file_name):
        output, _ = self.package_points()
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
