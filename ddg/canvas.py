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
from enum import Enum
import dataclasses
from dataclasses import dataclass
from ddg.config import AutoCompleteFile, DDConfig

from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets

completion = AutoCompleteFile()

class EditStyle(Enum):
    POINTS = 1
    RECTS = 2

@dataclass
class Scale:
    scale: float = 1
    unit: str = "px"
    top: int = 0
    left: int = 0

    @staticmethod
    def from_dict(dictionary):
        scale = Scale()
        fields = dataclasses.fields(Scale)
        for field in fields:
            setattr(scale, field.name, dictionary.get(field.name, field.default))
        return scale

class Attributes(dict):
    DEFAULT_KEYS = ["Name", "Partnumber", "Description", "Short Description", "Manufacturer", "Marking", "Datasheet", "Length", "Width", "Height", "Weight", "Package", "IO/Pin Count"]
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
    DEFAULT_COLORS = {"Resistor":QtGui.QColor(QtCore.Qt.black), "Capacitor":QtGui.QColor(QtCore.Qt.gray), "Crystal":QtGui.QColor(QtCore.Qt.green), 
                      "Diode": QtGui.QColor(QtCore.Qt.blue), "Inductor":QtGui.QColor(QtCore.Qt.cyan), "Integrated Circuit":QtGui.QColor(QtCore.Qt.yellow).darker(200), 
                      "Transistor":QtGui.QColor(QtCore.Qt.darkYellow), "Discrete < 3 Pins":QtGui.QColor(QtCore.Qt.magenta), 
                      "Discrete > 3 Pins":QtGui.QColor(QtCore.Qt.darkMagenta), "Connectors":QtGui.QColor(QtCore.Qt.cyan)}

    def __init__(self):
        from collections import defaultdict
        QtWidgets.QGraphicsScene.__init__(self)
        self.reset()

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
            self.colors[class_name] = Canvas.DEFAULT_COLORS.get(category, QtGui.QColor(QtCore.Qt.black))
            self.class_attributes[class_name] = a
            self.class_visibility[class_name] = True

    def add_category(self, name):
        if name not in self._categories:
            self.data[name] = []
            self._categories.append(name)

    def add_point(self, point):

        if self.edit_style != EditStyle.POINTS:
            return

        if self.current_image_name is None or self.current_class_name is None:
            return

        if not self.class_visibility[self.current_class_name]:
            return

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
            
    def clear_measures(self):
        for graphic in self.items():
            if type(graphic) == QtWidgets.QGraphicsPathItem:
                self.removeItem(graphic)
            elif type(graphic) == QtWidgets.QGraphicsTextItem:
                self.removeItem(graphic)

    def clear_selection(self):
        self.selection = []
        if self.edit_style == EditStyle.RECTS:
            self.clear_measures()
            self.display_measures()
        elif self.edit_style == EditStyle.POINTS:
            self.clear_points()
            self.display_points()

    def delete_selected_points(self):
        if self.current_image_name is not None:
            if self.edit_style == EditStyle.POINTS:
                points = self.points[self.current_image_name]
                for class_name, point in self.selection:
                    points[class_name].remove(point)
                    count = 0
                    for image in self.points.keys():
                        count += len(self.points[image][class_name])
                    self.update_point_count.emit(self.current_image_name, class_name, count)
                self.selection = []
                self.display_points()
            elif self.edit_style == EditStyle.RECTS:
                mrects = self.measure_rects[self.current_image_name]
                for selected in self.selection:
                    for i, mrect in enumerate(mrects):
                        if selected == mrect:
                            self.measure_rects[self.current_image_name].pop(i)
                            self.measure_rects_data[self.current_image_name].pop(i)
                            break
                self.selection = []
                self.display_measures()


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
        if self.edit_style != EditStyle.POINTS:
            return
        self.clear_points()
        if self.current_image_name in self.points:
            display_radius = self.ui['point']['radius']
            active_color = QtGui.QColor(self.ui['point']['color'][0], self.ui['point']['color'][1], self.ui['point']['color'][2])
            active_brush = QtGui.QBrush(active_color, QtCore.Qt.SolidPattern)
            active_pen = QtGui.QPen(active_brush, 2)
            for class_name in self.points[self.current_image_name]:
                if not self.class_visibility[class_name]:
                    continue
                points = self.points[self.current_image_name][class_name]
                brush = QtGui.QBrush(self.colors[class_name], QtCore.Qt.SolidPattern)
                pen = QtGui.QPen(brush, 2)
                for point in points:
                    if class_name == self.current_class_name:
                        self.addEllipse(QtCore.QRectF(point.x() - ((display_radius - 1) / 2), point.y() - ((display_radius - 1) / 2), display_radius, display_radius), active_pen, active_brush)
                    else:
                        self.addEllipse(QtCore.QRectF(point.x() - ((display_radius - 1) / 2), point.y() - ((display_radius - 1) / 2), display_radius, display_radius), pen, brush)

    def display_measures(self):
        if self.current_image_name is None:
            return
        if self.edit_style != EditStyle.RECTS:
            return
        self.clear_measures()

        white = QtGui.QColor(255, 255, 255)
        color = QtGui.QColor(self.ui['point']['color'][0], self.ui['point']['color'][1], self.ui['point']['color'][2])
        brush = QtGui.QBrush(color, QtCore.Qt.SolidPattern)
        pen = QtGui.QPen(brush, 2)

        image_scale = self.image_scale.get(self.current_image_name, Scale())
        scale = image_scale.scale
        unit = image_scale.unit

        mrects = self.measure_rects[self.current_image_name].copy()
        mrects_data = self.measure_rects_data[self.current_image_name].copy()
        self.measure_rects[self.current_image_name] = []
        self.measure_rects_data[self.current_image_name] = []
        for mrect in mrects_data:
            x = mrect["x"]
            y = mrect["y"]
            width = mrect["width"]
            height = mrect["height"]
            ppath = QtGui.QPainterPath()
            ppath.setFillRule(QtCore.Qt.WindingFill)
            ppath.addRect(x, y, width, height)
            path = self.addPath(ppath, pen)

            topItem = self.addText("{:.1f} {}".format(width*scale, unit))
            topItem.setDefaultTextColor(white)
            font = topItem.font()
            font.setBold(True)
            topItem.setFont(font)
            topItem.setPos(x, y)

            leftItem = self.addText("{:.1f} {}".format(height*scale, unit))
            leftItem.setDefaultTextColor(white)
            leftItem.setPos(x, y + leftItem.boundingRect().width() + topItem.boundingRect().height()*1.05)
            leftItem.setRotation(-90)
            font = leftItem.font()
            font.setBold(True)
            leftItem.setFont(font)
            self.measure_rects[self.current_image_name].append(path)
            self.measure_rects_data[self.current_image_name].append(mrect)

    def export_counts(self, file_name, survey_id):
        import csv
        with open(file_name, "w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            header = ["Image", "Category", "Component", "Count", "Description", "Manufacturer", "Partnumber", 
                    "Marking", "Package", "Length", "Width", "Height", "IO/Pin Count"]
            writer.writerow(header)
            for image in self.points.keys():
                for category in self.categories:
                    for class_name in self.data[category]:
                        count = len(self.points[image].get(class_name, []))
                        attr = self.class_attributes[class_name]
                        row = [image, category, class_name, count, attr["Description"], attr['Manufacturer'], 
                               attr["Partnumber"], attr["Marking"], attr["Package"], attr["Length"], attr["Width"], 
                               attr["Height"], attr["IO/Pin Count"]]
                        writer.writerow(row)

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
                message_box = QtWidgets.QMessageBox(self.parent())
                message_box.setText("Warning")
                message_box.setInformativeText('Working directory already set. Change current project?')
                message_box.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                message_box.setDefaultButton(QtWidgets.QMessageBox.Cancel)
                ret = message_box.exec()
                if ret == QtWidgets.QMessageBox.Cancel:
                    return
                else:
                    self.reset()
                    self.load(drop_list)
        elif ".pnt" in peek:
            self.load_points(peek)
        else:
            base_path = os.path.split(peek)[0]
            for entry in drop_list:
                file_name = entry.toLocalFile()
                path = os.path.split(file_name)[0]
                error = False
                message = ''
                if os.path.isdir(file_name):
                    message = 'Mix of files and directories detected. Load canceled.'
                    QtWidgets.QMessageBox.warning(self.parent(), 'Warning', message, QtWidgets.QMessageBox.Ok)
                    return
                if base_path != path:
                    message = 'Files from multiple directories detected. Load canceled.'
                    QtWidgets.QMessageBox.warning(self.parent(), 'Warning', message, QtWidgets.QMessageBox.Ok)
                    return
                if self.directory != '' and self.directory != path:
                    message_box = QtWidgets.QMessageBox(self.parent())
                    message_box.setText("Warning")
                    message_box.setInformativeText('Working directory already set. Change current project?')
                    message_box.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                    message_box.setDefaultButton(QtWidgets.QMessageBox.Cancel)
                    ret = message_box.exec()
                    if ret == QtWidgets.QMessageBox.Cancel:
                        return
                    else:
                        self.reset()
                        self.load(drop_list)
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
            if self.edit_style == EditStyle.POINTS:
                self.display_points()
            elif self.edit_style == EditStyle.RECTS:
                self.display_measures()
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
        self.reset()
        file = open(file_name, 'r')
        self.directory = os.path.split(file_name)[0]
        self.directory_set.emit(self.directory)
        data = json.load(file)
        file.close()
        survey_id = data['metadata']['survey_id']

        self.class_attributes = data["attributes"]
        for class_name, attributes in self.class_attributes.items():
            if attributes["Package"] not in completion.packages:
                completion.update(packages=[attributes["Package"]])
            if attributes["Manufacturer"] not in completion.manufacturers:
                completion.update(manufacturers=[attributes["Manufacturer"]])
        # Backward compat
        if 'ui' in data:
            self.ui = data['ui']
        else:
            self.ui = {'grid': {'size': 200, 'color': [255, 255, 255]}, 'point': {'radius': 25, 'color': [255, 255, 0]}}
        # End Backward compat

        self.coordinates = data["pcb_data"].copy()
        self.colors = data['colors'].copy()
        self.data = data['data'].copy()
        self._categories = list(self.data.keys())
        self.points = {}
        if 'points' in data:
            self.points = data['points']
        self.class_visibility = data['visibility']
        image_scale = data['image_scale']
        for k, l in image_scale.items():
            new_list = []
            for scale_dict in l:
                new_list.append(Scale.from_dict(scale_dict))
            self.image_scale[k] = new_list

        for image in self.points:
            for class_name in self.points[image]:
                for p in range(len(self.points[image][class_name])):
                    point = self.points[image][class_name][p]
                    self.points[image][class_name][p] = QtCore.QPointF(point['x'], point['y'])
        for class_name in data['colors']:
            self.colors[class_name] = QtGui.QColor(self.colors[class_name][0], self.colors[class_name][1], self.colors[class_name][2])
        for image in data["measures"]:
            for rect in data["measures"][image]:
                x = rect['x']
                y = rect['y']
                w = rect['w']
                h = rect['h']
                qrect = QtCore.QRectF(x, y, w, h)
                ppath = QtGui.QPainterPath()
                ppath.setFillRule(QtCore.Qt.WindingFill)
                ppath.addRect(qrect)
                path = QtWidgets.QGraphicsPathItem(ppath)
                self.measure_rects[image].append(path)
                self.measure_rects_data[image].append({"x":x, "y":y, "width":w, "height":h})

        self.points_loaded.emit(survey_id)
        self.fields_updated.emit()
        path = os.path.split(file_name)[0]
        if self.points.keys():
            path = os.path.join(path, list(self.points.keys())[0])
            self.load_image(path)

    def measure_area(self, rect):
        if self.current_image_name is None or self.edit_style != EditStyle.RECTS:
            return

        image_scale = self.image_scale.get(self.current_image_name, Scale)

        topLeft = rect.topLeft()
        bottomRight = rect.bottomRight()
        width = bottomRight.x() - topLeft.x()
        height = bottomRight.y() - topLeft.y()
        scale = image_scale.scale
        unit = image_scale.unit

        active_color = QtGui.QColor(self.ui['point']['color'][0], self.ui['point']['color'][1], self.ui['point']['color'][2])
        active_brush = QtGui.QBrush(active_color, QtCore.Qt.SolidPattern)
        active_pen = QtGui.QPen(active_brush, 2)

        ppath = QtGui.QPainterPath()
        ppath.setFillRule(QtCore.Qt.WindingFill)
        ppath.addRect(rect)
        path = self.addPath(ppath, active_pen)

        topItem = self.addText("{:.1f} {}".format(width*scale, unit))
        topItem.setDefaultTextColor(QtGui.QColor(255, 255, 255))
        font = topItem.font()
        font.setBold(True)
        topItem.setFont(font)
        topItem.setPos(topLeft.x(), topLeft.y())

        leftItem = self.addText("{:.1f} {}".format(height*scale, unit))
        leftItem.setDefaultTextColor(QtGui.QColor(255, 255, 255))
        leftItem.setPos(topLeft.x(), topLeft.y() + leftItem.boundingRect().width() + topItem.boundingRect().height()*1.05)
        leftItem.setRotation(-90)
        font = leftItem.font()
        font.setBold(True)
        leftItem.setFont(font)
        self.measure_rects[self.current_image_name].append(path)
        self.measure_rects_data[self.current_image_name].append({"x":topLeft.x(), "y":topLeft.y(), "width":width, "height":height})

    def package_points(self, survey_id):
        count = 0
        image_scale = {}
        for k, l in self.image_scale.items():
            new_list = [dataclasses.asdict(scale) for scale in l]
            image_scale[k] = new_list

        for class_name, attributes in self.class_attributes.items():
            if attributes["Package"] not in completion.packages:
                completion.update(packages=[attributes["Package"]])
            if attributes["Manufacturer"] not in completion.manufacturers:
                completion.update(manufacturers=[attributes["Manufacturer"]])

        package = {'data': {}, 'points': {}, 'colors': {}, 'pcb_data': self.coordinates, 
                   'metadata': {'survey_id': survey_id}, 'attributes': self.class_attributes, 'ui': self.ui, 
                   'visibility': self.class_visibility, 'image_scale': image_scale, 'measures': {}}
        package['data'] = self.data.copy()
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
        for image in self.measure_rects_data:
            package['measures'][image] = []
            for mrect in self.measure_rects_data[image]:
                measure_data = {}
                measure_data['x'] = mrect["x"]
                measure_data['y'] = mrect["y"]
                measure_data['w'] = mrect["width"]
                measure_data['h'] = mrect["height"]
                package['measures'][image].append(measure_data)
        
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
        self.data[new_category] = self.data.pop(old_category)
        index = self._categories.index(old_category)
        self._categories.pop(index)
        self._categories.insert(index, new_category)
        self.current_category_name = new_category

    def move_class(self, classname, old_category, new_category, index=None):
        if new_category not in self.categories or old_category not in self.categories:
            raise ValueError("Category not found {}".format(new_category))
        if classname not in self.classes:
            raise ValueError("New name not found {}".format(classname))

        classes = self.data[old_category]
        index  = classes.index(classname)
        to_move = classes.pop(index)
        self.data[old_category] = classes
        if index is None:
            self.data[new_category].append(to_move)
        else:
            self.data[new_category].insert(index, to_move)
        self.display_points()

    def rename_class(self, old_class, new_class):
        if new_class in self.classes:
            raise ValueError("New name already exists {}".format(new_class))

        for k, v in self.data.items():
            if old_class in v:
                category = k
                break

        classes = self.data[category]
        index  = classes.index(old_class)
        classes.pop(index)
        classes.insert(index, new_class)
        self.data[category] = classes
        self.colors[new_class] = self.colors.pop(old_class)
        self.class_visibility[new_class] = self.class_visibility[old_class]
        self.class_attributes[new_class] = self.class_attributes[old_class]
        del self.class_attributes[old_class]
        del self.class_visibility[old_class]
        
        for image in self.points:
            if old_class in self.points[image] and new_class in self.points[image]:
                self.points[image][new_class] += self.points[image].pop(old_class)
            elif old_class in self.points[image]:
                self.points[image][new_class] = self.points[image].pop(old_class)
        self.current_class_name = new_class
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
        del self.class_visibility[name]
        self.display_points()

    def remove_category(self, name):
        classes = self.data[name]
        for image in self.points:
            for class_name in classes:
                del self.class_attributes[class_name]
                del self.class_visibility[class_name]
                if class_name in self.points[image]:
                    del self.points[image][class_name]
        self.current_category_name = None
        self.current_class_name = None
        del self.data[name]
        self._categories.pop(self._categories.index(name))
        self.display_points()

    def reset(self):
        from collections import defaultdict
        from ddg.config import DDConfig

        self.config = DDConfig(DDConfig.DEFAULTFILE)
        self.points = {}
        self.class_visibility = {} # to be implemented
        self.colors = {}
        self.coordinates = {}

        self._categories = self.config.categories.copy() 
        self.class_attributes = {}
        self.data = {}
        for c in self._categories:
            self.data[c] = [] # classes
        self.previous_class_name = None
        self.next_class_name = None

        self.selection = []
        self.edit_style = EditStyle.POINTS
        self.ui = self.config.ui.copy()

        self.directory = ''
        self.current_image_name = None
        self.current_class_name = None
        self.current_category_name = None
        self.current_selection = None

        self.qt_image = None
        self.show_grid = True

        self.selected_pen = QtGui.QPen(QtGui.QBrush(QtCore.Qt.red, QtCore.Qt.SolidPattern), 1)

        self.image_scale = defaultdict(dict)
        self.measure_rects = defaultdict(list) # here we sore the QGraphicsPathItems
        self.measure_rects_data = defaultdict(list) # here we store the x, y, w, h of the measured rects. PathItems are destroyed when updating the view therefore we need to store that info seperately
        self.timer = None

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
            completion.write(AutoCompleteFile.DEFAULTFILE)
        except OSError:
            return False
        return True

    def select_points(self, rect):
        self.selection = []
        if self.edit_style == EditStyle.POINTS:
            self.display_points()
            current = self.points[self.current_image_name]
            display_radius = self.ui['point']['radius']
            for class_name in current:
                for point in current[class_name]:
                    if rect.contains(point):
                        offset = ((display_radius + 6) // 2)
                        self.addEllipse(QtCore.QRectF(point.x() - offset, point.y() - offset, display_radius + 6, display_radius + 6), self.selected_pen)
                        self.selection.append((class_name, point))
        elif self.edit_style == EditStyle.RECTS:
            color = QtGui.QColor(223, 23, 23)
            brush = QtGui.QBrush(color, QtCore.Qt.SolidPattern)
            pen = QtGui.QPen(brush, 4)
            for mrect in self.measure_rects[self.current_image_name]:
                if mrect.path().intersects(rect):
                    self.removeItem(mrect)
                    path = QtGui.QPainterPath()
                    path.setFillRule(QtCore.Qt.WindingFill)
                    path.addRect(mrect.boundingRect())
                    self.addPath(path, pen)
                    self.selection.append(mrect)

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

    def set_edit_style(self, edit_style):
        self.edit_style = edit_style
        if self.edit_style == EditStyle.POINTS:
            self.clear_measures()
            self.display_points()
        elif self.edit_style == EditStyle.RECTS:
            self.clear_points()
            self.display_measures()

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

    def set_scale(self, mm, rect):
        if self.current_image_name is None:
            return
        scale = int(mm)/int(rect.width())
        topLeft = rect.topLeft()
        if self.current_image_name not in self.image_scale.keys():
            self.image_scale[self.current_image_name] = Scale()
        self.image_scale[self.current_image_name].scale = scale
        self.image_scale[self.current_image_name].unit = "mm"
        self.image_scale[self.current_image_name].top = topLeft.y()*scale
        self.image_scale[self.current_image_name].left = topLeft.x()*scale
        self.display_measures()

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
