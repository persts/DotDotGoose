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
from PyQt5 import QtCore, QtWidgets, uic

from mc import Canvas
from mc import PointWidget

# from .ui_central_widget import Ui_central as CLASS_DIALOG
CLASS_DIALOG, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'central_widget.ui'))


class CentralWidget(QtWidgets.QDialog, CLASS_DIALOG):

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

    def resizeEvent(self, theEvent):
        self.graphicsView.fitInView(self.canvas.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        self.graphicsView.setSceneRect(self.canvas.itemsBoundingRect())
