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
import sys
import os
from PyQt5.QtWidgets import QMainWindow, QMenuBar, QMenu, QAction, QMessageBox
from PyQt5 import QtWidgets
from ddg import CentralWidget
from ddg.canvas import EditStyle
from ddg import __version__

# _TITLE_STRING = 'DotDotGoose [v {}] - Center for Biodiversity and Conservation ( http://cbc.amnh.org )'.format(__version__)
_TITLE_STRING = 'DotDotIC [v {}] - ECS / A2MAC1 '.format(__version__)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_TITLE_STRING)
        self._centralWidget = CentralWidget()
        self.setCentralWidget(self._centralWidget)
        self.show()
        self.resize(int(screen.width() * .90), int(screen.height() * 0.90))
        self.move(int(screen.width() * .05) // 2, 0)

        self._createActions()
        self._createMenuBar()
    
    def _createMenuBar(self):
        menuBar= self.menuBar()
        # --- File menu
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.exportCountsAction)
        fileMenu.addAction(self.exportDetailsAction)

        # --- Edit menu
        editMenu = QMenu("&Edit", self)
        menuBar.addMenu(editMenu)
        editMenu.addAction(self.editPointsAction)
        editMenu.addAction(self.editMeasureAction)

        # --- Help menu
        helpMenu = QMenu("&Help", self)
        menuBar.addMenu(helpMenu)
        helpMenu.addAction(self.infoAction)

    def _createActions(self):
        self.saveAction = QAction("Save Project", self)
        self.saveAction.triggered.connect(self._centralWidget.point_widget.save)
        self.openAction = QAction("Open Project/Points", self)
        self.openAction.triggered.connect(self.load)
        # import metadata merge in load project ?
        self.exportCountsAction = QAction("Export to Text (csv)", self)
        self.exportCountsAction.triggered.connect(self._centralWidget.point_widget.export_counts)
        self.exportDetailsAction = QAction("Export detail images", self)
        self.exportDetailsAction.triggered.connect(self._centralWidget.point_widget.export_details)
        
        self.infoAction = QAction("Info", self)
        self.infoAction.triggered.connect(self.display_info)

        self.editPointsAction = QAction("Edit Counts", self)
        self.editPointsAction.setCheckable(True)
        self.editPointsAction.setChecked(True)
        self.editPointsAction.triggered.connect(self.set_edit_points)
        self._centralWidget.pointsToolButton.setDefaultAction(self.editPointsAction)

        self.editMeasureAction = QAction("Edit Measurements", self)
        self.editMeasureAction.setCheckable(True)
        self.editMeasureAction.setChecked(False)
        self.editMeasureAction.triggered.connect(self.set_edit_rects)
        self._centralWidget.rectsToolButton.setDefaultAction(self.editMeasureAction)


    def display_info(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Info")
        msg.setText("Information about DotDotIC " + __version__)
        msgText = "Contact gstockinger@ecs-network.com for bug reports.\nDotDotIC is based in the fabulous DotDotGoose.\nPlease visit their website\nhttps://biodiversityinformatics.amnh.org/open_source/dotdotgoose !"
        msg.setInformativeText(msgText)
        msg.setStandardButtons(QMessageBox.Ok)
        _ = msg.exec_()
    
    def load(self):
        self._centralWidget.point_widget.load()
        self.set_edit_points()

    def set_edit_points(self):
        self.editPointsAction.setChecked(True)
        self.editMeasureAction.setChecked(False)
        self._centralWidget.pointsToolButton.setChecked(True)
        self._centralWidget.rectsToolButton.setChecked(False)
        self._centralWidget.canvas.set_edit_style(EditStyle.POINTS)

    def set_edit_rects(self):
        self.editMeasureAction.setChecked(True)
        self.editPointsAction.setChecked(False)
        self._centralWidget.pointsToolButton.setChecked(False)
        self._centralWidget.rectsToolButton.setChecked(True)
        self._centralWidget.canvas.set_edit_style(EditStyle.RECTS)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    if 'plastique' in QtWidgets.QStyleFactory().keys():
        app.setStyle(QtWidgets.QStyleFactory.create('plastique'))
    screen = app.desktop().availableGeometry()
    main = MainWindow()
    sys.exit(app.exec_())
