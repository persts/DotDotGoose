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
from PyQt5.QtWidgets import QDialog, QMainWindow, QMenu, QAction, QTextEdit, QVBoxLayout
from PyQt5 import QtWidgets
from ddg import CentralWidget
from ddg.canvas import EditStyle, recentlyUsed
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
        import os
        from functools import partial
        menuBar = self.menuBar()
        # --- File menu
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)
        fileMenu.addAction(self.quickSaveAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.openAction)
        recentlyUsedMenu = QMenu("Recently Used", fileMenu)

        if len(recentlyUsed.files) == 0:
            action = QAction("No files", self)
            action.setEnabled(False)
            recentlyUsedMenu.addAction(action)
        else:
            for f in recentlyUsed.files:
                fname = os.path.basename(f)
                action = QAction(f, self)
                action.triggered.connect(partial(self._centralWidget.canvas.load_points, f))
                recentlyUsedMenu.addAction(action)

        fileMenu.addMenu(recentlyUsedMenu)
        fileMenu.addSeparator()
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
        helpMenu.addAction(self.showControlsAction)

    def _createActions(self):
        self.saveAction = QAction("Save Project As...", self)
        self.saveAction.triggered.connect(self._centralWidget.point_widget.save)
        self.quickSaveAction = QAction("Save Project", self)
        self.quickSaveAction.triggered.connect(self._centralWidget.point_widget.quick_save)
        self.openAction = QAction("Open Project/Points", self)
        self.openAction.triggered.connect(self.load)
        # import metadata merge in load project ?
        self.exportCountsAction = QAction("Export to Text (csv)", self)
        self.exportCountsAction.triggered.connect(self._centralWidget.point_widget.export_counts)
        self.exportDetailsAction = QAction("Export detail images", self)
        self.exportDetailsAction.triggered.connect(self._centralWidget.point_widget.export_details)
        
        self.infoAction = QAction("Info", self)
        self.infoAction.triggered.connect(self.display_info)

        self.showControlsAction = QAction("Controls", self)
        self.showControlsAction.triggered.connect(self.display_controls)

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
        dialog = QDialog(self)
        dialog.setWindowTitle("Information about DotDotIC " + __version__)
        dialog.resize(500, 500)
        textEdit = QTextEdit(dialog, readOnly=True)
        textEdit.setHtml(
            """
            <html>
                <body>
                    <article>
                        <h2> Info </h2>                            
                        <p> Version: {} </p>
                        <p> Bugeports: gstockinger@ecs-network.com </p>
                        <h2> Disclaimer </h2>
                        <p> DotDotIC is based in the fabulous DotDotGoose. </p>
                        <p> Please visit their website\nhttps://biodiversityinformatics.amnh.org/open_source/dotdotgoose ! </p>
                        <p></p>
                    </article>
                </body>
            </html>
        """.format(__version__))
        layout = QVBoxLayout()
        layout.addWidget(textEdit)
        dialog.setLayout(layout)
        _ = dialog.show()

    def display_controls(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Controls")
        dialog.resize(500, 500)
        textEdit = QTextEdit(dialog, readOnly=True)
        textEdit.setHtml(
            """
            <html>
                <body>
                    <article>
                        <h2> General </h2>                            
                        <p> There are two modes for counting or measuring which can be selected in the toolbar. </p>
                        <p> STRG + +             - Add component to current category    </p>
                        <h2> Count Mode </h2>
                        <p> STRG + Right Click   - Add Count    </p>
                        <p> SHIFT + Drag         - Select Items </p>
                        <p> DEL (With Selection) - Delete Items </p>
                        <p></p>
                        <h2> Measure Mode </h2>
                        <p> C + Drag             - Calibrate Scale </p>
                        <p> M + Drag             - Measure         </p>
                        <p> SHIFT + Drag         - Select Items    </p>
                        <p> DEL (With Selection) - Delete Items    </p>
                    </article>
                </body>
            </html>
        """)
        layout = QVBoxLayout()
        layout.addWidget(textEdit)
        dialog.setLayout(layout)
        _ = dialog.show()
    
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
