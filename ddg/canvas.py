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
import glob
import numpy as np

from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets

class Attributes(dict):
    DEFAULT_KEYS = ["Name", "Partnumber", "Description", "Short Description", "Manufacturer", "Marking", "Datasheet", "Length", "Width", "Height", "Weight", "Package"]
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        for k in Attributes.DEFAULT_KEYS:
            self[k] = ""

    def __delitem__(self, k):
        if not k in Attributes.DEFAULT_KEYS:
            if self.has_key(k):
                dict.__delitem__(self, k)

class Canvas(QtWidgets.QGraphicsScene):
    image_loaded = QtCore.pyqtSignal(str, str)
    points_loaded = QtCore.pyqtSignal(str)
    directory_set = QtCore.pyqtSignal(str)
    fields_updated = QtCore.pyqtSignal()
    points_updated = QtCore.pyqtSignal()
    update_point_count = QtCore.pyqtSignal(str, str, int)

    def __init__(self):
        from collections import defaultdict, OrderedDict
        QtWidgets.QGraphicsScene.__init__(self)
        # dictionary for saving points: Structured like points[image_name][class_name] = [list of points]
        self.points = {}
        self.visible_points = {} # to be implemented
        self.colors = {}
        self.coordinates = {}

        self._categories = ["Resistor", "Capacitor", "Crystal", "Diode", "Inductor", "Integrated Circuit", "Transistor", "Discrete < 3 Pins", "Discrete > 3 Pins"]
        self.class_attributes = {}
        self.data = {}
        for c in self._categories:
            self.data[c] = [] # classes
        self.previous_class_name = None
        self.next_class_name = None

        self.selection = []
        self.ui = {'grid': {'size': 200, 'color': [255, 255, 255]}, 'point': {'radius': 25, 'color': [255, 255, 0]}}

        self.directory = ''
        self.current_image_name = None
        self.current_class_name = None
        self.current_category_name = None
        self.current_selection = None

        self.qt_image = None
        self.show_grid = True

        self.selected_pen = QtGui.QPen(QtGui.QBrush(QtCore.Qt.red, QtCore.Qt.SolidPattern), 1)

    @property
    def classes(self):
        classes = []
        for _, v in self.data.items():
            classes.extend(v)
        return classes

    def add_class(self, category, class_name):
        if class_name not in self.classes:
            a = Attributes()
            a["Name"] = class_name
            self.data[category].append(class_name)
            self.colors[class_name] = QtGui.QColor(QtCore.Qt.black)
            self.class_attributes[class_name] = a

    def add_category(self, name):
        if name not in self._categories:
            self.data[name] = []
            self._categories.append(name)

    def add_point(self, point):
        if self.current_image_name is not None and self.current_class_name is not None:
            for image in self.points.keys():
                if self.current_class_name not in self.points[image]:
                    self.points[image][self.current_class_name] = []
            display_radius = self.ui['point']['radius']
            active_color = QtGui.QColor(self.ui['point']['color'][0], self.ui['point']['color'][1], self.ui['point']['color'][2])
            active_brush = QtGui.QBrush(active_color, QtCore.Qt.SolidPattern)
            active_pen = QtGui.QPen(active_brush, 2)
            self.points[self.current_image_name][self.current_class_name].append(point)
            count = 0
            for image in self.points.keys():
                count += len(self.points[image][self.current_class_name])
            self.addEllipse(QtCore.QRectF(point.x() - ((display_radius - 1) / 2), point.y() - ((display_radius - 1) / 2), display_radius, display_radius), active_pen, active_brush)
            self.update_point_count.emit(self.current_image_name, self.current_class_name, count)

    @property
    def categories(self):
        i1 = list(sorted(self.data.keys()))
        i2 = list(sorted(self._categories))
        assert i1 == i2
        return self._categories

    def clear_grid(self):
        for graphic in self.items():
            if type(graphic) == QtWidgets.QGraphicsLineItem:
                self.removeItem(graphic)

    def clear_points(self):
        for graphic in self.items():
            if type(graphic) == QtWidgets.QGraphicsEllipseItem:
                self.removeItem(graphic)

    def delete_selected_points(self):
        if self.current_image_name is not None:
            points = self.points[self.current_image_name]
            for class_name, point in self.selection:
                points[class_name].remove(point)
                count = 0
                for image in self.points.keys():
                    count += len(self.points[image][class_name])
                self.update_point_count.emit(self.current_image_name, class_name, count)
            self.selection = []
            self.display_points()

    def display_grid(self):
        self.clear_grid()
        if self.current_image_name and self.show_grid:
            grid_color = QtGui.QColor(self.ui['grid']['color'][0], self.ui['grid']['color'][1], self.ui['grid']['color'][2])
            grid_size = self.ui['grid']['size']
            rect = self.itemsBoundingRect()
            brush = QtGui.QBrush(grid_color, QtCore.Qt.SolidPattern)
            pen = QtGui.QPen(brush, 1)
            for x in range(grid_size, int(rect.width()), grid_size):
                line = QtCore.QLineF(x, 0.0, x, rect.height())
                self.addLine(line, pen)
            for y in range(grid_size, int(rect.height()), grid_size):
                line = QtCore.QLineF(0.0, y, rect.width(), y)
                self.addLine(line, pen)

    def display_points(self):
        self.clear_points()
        if self.current_image_name in self.points:
            display_radius = self.ui['point']['radius']
            active_color = QtGui.QColor(self.ui['point']['color'][0], self.ui['point']['color'][1], self.ui['point']['color'][2])
            active_brush = QtGui.QBrush(active_color, QtCore.Qt.SolidPattern)
            active_pen = QtGui.QPen(active_brush, 2)
            for class_name in self.points[self.current_image_name]:
                points = self.points[self.current_image_name][class_name]
                brush = QtGui.QBrush(self.colors[class_name], QtCore.Qt.SolidPattern)
                pen = QtGui.QPen(brush, 2)
                for point in points:
                    if class_name == self.current_class_name:
                        self.addEllipse(QtCore.QRectF(point.x() - ((display_radius - 1) / 2), point.y() - ((display_radius - 1) / 2), display_radius, display_radius), active_pen, active_brush)
                    else:
                        self.addEllipse(QtCore.QRectF(point.x() - ((display_radius - 1) / 2), point.y() - ((display_radius - 1) / 2), display_radius, display_radius), pen, brush)

    def export_counts(self, file_name, survey_id):
        import csv
        with open(file_name, "w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            for image in self.points.keys():
                for category in self.categories:
                    for class_name in self.data[category]:
                        count = len(self.points[image].get(class_name, []))
                        row = [image, category, class_name, count]
                        writer.writerow(row)

    def get_custom_field_data(self):
        data = {}
        if self.current_image_name is not None:
            for field_def in self.custom_fields['fields']:
                if self.current_image_name in self.custom_fields['data'][field_def[0]]:
                    data[field_def[0]] = self.custom_fields['data'][field_def[0]][self.current_image_name]
                else:
                    data[field_def[0]] = ''
        return data

    def get_category_from_class(self, class_name):
        category = None
        for c, v in self.data.items():
            if class_name in v:
                category = c
                break
        return category

    def load(self, drop_list):
        peek = drop_list[0].toLocalFile()
        if os.path.isdir(peek):
            if self.directory == '':
                # strip off trailing sep from path
                osx_hack = os.path.join(peek, 'OSX')
                self.directory = os.path.split(osx_hack)[0]
                # end
                self.directory_set.emit(self.directory)
                files = glob.glob(os.path.join(self.directory, '*'))
                image_format = [".jpg", ".jpeg", ".png", ".tif"]
                f = (lambda x: os.path.splitext(x)[1].lower() in image_format)
                image_list = list(filter(f, files))
                image_list = sorted(image_list)
                self.load_images(image_list)
            else:
                QtWidgets.QMessageBox.warning(self.parent(), 'Warning', 'Working directory already set. Load canceled.', QtWidgets.QMessageBox.Ok)
        else:
            base_path = os.path.split(peek)[0]
            for entry in drop_list:
                file_name = entry.toLocalFile()
                path = os.path.split(file_name)[0]
                error = False
                message = ''
                if os.path.isdir(file_name):
                    error = True
                    message = 'Mix of files and directories detected. Load canceled.'
                if base_path != path:
                    error = True
                    message = 'Files from multiple directories detected. Load canceled.'
                if self.directory != '' and self.directory != path:
                    error = True
                    message = 'Image originated outside current working directory. Load canceled.'
                if error:
                    QtWidgets.QMessageBox.warning(self.parent(), 'Warning', message, QtWidgets.QMessageBox.Ok)
                    return None
            self.directory = base_path
            self.directory_set.emit(self.directory)
            self.load_images(drop_list)

    def load_image(self, in_file_name):
        Image.MAX_IMAGE_PIXELS = 1000000000
        file_name = in_file_name
        if type(file_name) == QtCore.QUrl:
            file_name = in_file_name.toLocalFile()

        if self.directory == '':
            self.directory = os.path.split(file_name)[0]
            self.directory_set.emit(self.directory)

        if self.directory == os.path.split(file_name)[0]:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.selection = []
            self.clear()
            self.current_image_name = os.path.split(file_name)[1]
            if self.current_image_name not in self.points.keys():
                self.points[self.current_image_name] = {}
            try:
                img = Image.open(file_name)
                channels = len(img.getbands())
                array = np.array(img)
                img.close()
                if array.shape[0] > 10000 or array.shape[1] > 10000:
                    # Make smaller tiles to save memory
                    stride = 100
                    max_stride = (array.shape[1] // stride) * stride
                    tail = array.shape[1] - max_stride
                    tile = np.zeros((array.shape[0], stride, array.shape[2]), dtype=np.uint8)
                    for s in range(0, max_stride, stride):
                        tile[:, :] = array[:, s:s + stride]
                        qt_image = QtGui.QImage(tile.data, tile.shape[1], tile.shape[0], QtGui.QImage.Format_RGB888)
                        pixmap = QtGui.QPixmap.fromImage(qt_image)
                        item = self.addPixmap(pixmap)
                        item.moveBy(s, 0)
                    # Fix for windows, thin slivers at the end cause the app to hang. QImage bug?
                    if tail > 0:
                        tile2 = np.ones((array.shape[0], stride, array.shape[2]), dtype=np.uint8) * 255
                        tile2[:, 0:tail] = array[:, max_stride:array.shape[1]]
                        qt_image = QtGui.QImage(tile2.data, tile2.shape[1], tile2.shape[0], QtGui.QImage.Format_RGB888)
                        pixmap = QtGui.QPixmap.fromImage(qt_image)
                        item = self.addPixmap(pixmap)
                        item.moveBy(max_stride, 0)
                else:
                    if channels == 1:
                        self.qt_image = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_Grayscale8)
                    else:
                        # Apply basic min max stretch to the image
                        for chan in range(channels):
                            array[:, :, chan] = np.interp(array[:, :, chan], (array[:, :, chan].min(), array[:, :, chan].max()), (0, 255))
                        bpl = int(array.nbytes / array.shape[0])
                        if array.shape[2] == 4:
                            self.qt_image = QtGui.QImage(array.data, array.shape[1], array.shape[0], QtGui.QImage.Format_RGBA8888)
                        else:
                            self.qt_image = QtGui.QImage(array.data, array.shape[1], array.shape[0], bpl, QtGui.QImage.Format_RGB888)
                    self.pixmap = QtGui.QPixmap.fromImage(self.qt_image)
                    self.addPixmap(self.pixmap)
            except FileNotFoundError:
                QtWidgets.QMessageBox.critical(None, 'File Not Found', '{} is not in the same folder as the point file.'.format(self.current_image_name))
                self.image_loaded.emit(self.directory, self.current_image_name)
            self.image_loaded.emit(self.directory, self.current_image_name)
            self.display_points()
            self.display_grid()
            QtWidgets.QApplication.restoreOverrideCursor()

    def load_images(self, images):
        for file in images:
            file_name = file
            if type(file) == QtCore.QUrl:
                file_name = file.toLocalFile()

            image_name = os.path.split(file_name)[1]
            if image_name not in self.points:
                self.points[image_name] = {}
        if len(images) > 0:
            self.load_image(images[0])

    def load_points(self, file_name):
        file = open(file_name, 'r')
        self.directory = os.path.split(file_name)[0]
        self.directory_set.emit(self.directory)
        data = json.load(file)
        file.close()
        survey_id = data['metadata']['survey_id']

        self.class_attributes = data["attributes"]
        # Backward compat
        if 'ui' in data:
            self.ui = data['ui']
        else:
            self.ui = {'grid': {'size': 200, 'color': [255, 255, 255]}, 'point': {'radius': 25, 'color': [255, 255, 0]}}
        # End Backward compat

        self.colors = data['colors']
        self.data = data['data']
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
        self.fields_updated.emit()
        path = os.path.split(file_name)[0]
        if self.points.keys():
            path = os.path.join(path, list(self.points.keys())[0])
            self.load_image(path)

    def package_points(self, survey_id):
        count = 0
        package = {'data': {}, 'points': {}, 'colors': {}, 'metadata': {'survey_id': survey_id}, 'attributes': self.class_attributes, 'ui': self.ui}
        package['data'] = self.data
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
            self.points_updated.emit()

    def rename_category(self, old_category, new_category):
        if new_category in self.categories:
            raise ValueError("New name already exists {}".format(new_category))
        self.data[new_category] = self.data[old_category]
        index = self._categories.index(old_category)
        self._categories.pop(index)
        self._categories.insert(index, new_category)
        del self.data[old_category]

    def rename_class(self, old_class, new_class):
        if new_class in self.classes:
            raise ValueError("New name already exists {}".format(new_class))

        for k, v in self.data.items():
            if old_class in v:
                category = k

        classes = self.data[category]
        index  = classes.index(old_class)
        classes.pop(index)
        classes.insert(index, new_class)
        self.data[category] = classes
        self.colors[new_class] = self.colors.pop(old_class)
        self.class_attributes[new_class] = self.class_attributes[old_class]
        del self.class_attributes[old_class]
        
        for image in self.points:
            if old_class in self.points[image] and new_class in self.points[image]:
                self.points[image][new_class] += self.points[image].pop(old_class)
            elif old_class in self.points[image]:
                self.points[image][new_class] = self.points[image].pop(old_class)
        self.display_points()
        
    def remove_class(self, name):
        category = self.get_category_from_class(name)
        for image in self.points:
            if name in self.points[image]:
                del self.points[image][name]
        classes = self.data[category]
        classes.pop(classes.index(name))
        self.data[category] = classes
        del self.class_attributes[name]
        self.current_class_name = None
        self.display_points()

    def remove_category(self, name):
        classes = self.data[name]
        for image in self.points:
            for class_name in classes:
                del self.class_attributes[class_name]
                if class_name in self.points[image]:
                    del self.points[image][class_name]
        self.current_category_name = None
        self.current_class_name = None
        del self.data[name]
        self._categories.pop(self._categories.index(name))
        self.display_points()

    def save_coordinates(self, x, y):
        if self.current_image_name is not None:
            if self.current_image_name not in self.coordinates:
                self.coordinates[self.current_image_name] = {'x': '', 'y': ''}
            self.coordinates[self.current_image_name]['x'] = x
            self.coordinates[self.current_image_name]['y'] = y

    def save_points(self, file_name, survey_id):
        try:
            output, _ = self.package_points(survey_id)
            file = open(file_name, 'w')
            json.dump(output, file)
            file.close()
        except OSError:
            return False
        return True

    def select_points(self, rect):
        self.selection = []
        self.display_points()
        current = self.points[self.current_image_name]
        display_radius = self.ui['point']['radius']
        for class_name in current:
            for point in current[class_name]:
                if rect.contains(point):
                    offset = ((display_radius + 6) // 2)
                    self.addEllipse(QtCore.QRectF(point.x() - offset, point.y() - offset, display_radius + 6, display_radius + 6), self.selected_pen)
                    self.selection.append((class_name, point))

    def set_current_class(self, class_name):
        if class_name in self.classes:
            self.current_class_name = class_name
            category = self.get_category_from_class(class_name)
            if category: self.set_current_category(category)
        else:
            self.current_class_name = None
        self.display_points()

    def set_current_category(self, category):
        self.current_category_name = category

    def set_grid_color(self, color):
        self.ui['grid']['color'] = [color.red(), color.green(), color.blue()]
        self.display_grid()

    def set_grid_size(self, size):
        self.ui['grid']['size'] = size
        self.display_grid()

    def set_point_color(self, color):
        self.ui['point']['color'] = [color.red(), color.green(), color.blue()]
        self.display_points()

    def set_point_radius(self, radius):
        self.ui['point']['radius'] = radius
        self.display_points()

    def toggle_grid(self, display):
        if display:
            self.show_grid = True
            self.display_grid()
        else:
            self.show_grid = False
            self.clear_grid()

    def toggle_points(self, display):
        if display:
            self.display_points()
            self.selection = []
        else:
            self.clear_points()
            
    def set_component_attribute(self, attribute, value):
        if self.current_class_name is not None:
            self.class_attributes[self.current_class_name][attribute] = value
            # self.fields_updated.emit()
