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
from PyQt6 import QtWidgets, QtCore, uic
from ddg import __version__

# from .ui_central_widget import Ui_central as CLASS_DIALOG
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(__file__)
CLASS_DIALOG, _ = uic.loadUiType(os.path.join(bundle_dir, 'about_dialog.ui'))


class AboutDialog(QtWidgets.QDialog, CLASS_DIALOG):

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        self.groupBoxDevelopers.setLayout(QtWidgets.QVBoxLayout())
        self.groupBoxContributors.setLayout(QtWidgets.QVBoxLayout())
        self.groupBoxTranslators.setLayout(QtWidgets.QVBoxLayout())

        self.labelVersion.setText(__version__)

        entry = QtWidgets.QLabel('Peter J. Ersts, {}'.format(self.tr('Center for Biodiversity and Conservation')))
        font = entry.font()
        font.setPointSize(10)
        entry.setFont(font)
        self.groupBoxDevelopers.layout().addWidget(entry)

        entry = QtWidgets.QLabel('Ido Senesh, https://github.com/idoadse')
        entry.setFont(font)
        self.groupBoxContributors.layout().addWidget(entry)

        entry = QtWidgets.QLabel('Julie Young, https://github.com/julieyoung6')
        entry.setFont(font)
        self.groupBoxContributors.layout().addWidget(entry)

        entry = QtWidgets.QLabel('Ștefan Istrate, https://github.com/stefanistrate')
        entry.setFont(font)
        self.groupBoxContributors.layout().addWidget(entry)

        entry = QtWidgets.QLabel('{} : Julie Young, [{}] {}, https://github.com/julieyoung6'.format(self.tr('Chinese (Mandarin)'), self.tr('Intern'), self.tr('Center for Biodiversity and Conservation')))
        entry.setFont(font)
        self.groupBoxTranslators.layout().addWidget(entry)

        entry = QtWidgets.QLabel('{} : Adrien Charbonneau, https://github.com/Adri-Charbonneau '.format(self.tr('French')))
        entry.setFont(font)
        self.groupBoxTranslators.layout().addWidget(entry)

        entry = QtWidgets.QLabel('{} : Mary Blair & Daniel López Lozano, {}'.format(self.tr('Spanish'), self.tr('Center for Biodiversity and Conservation')))
        entry.setFont(font)
        self.groupBoxTranslators.layout().addWidget(entry)

        entry = QtWidgets.QLabel('{} : Nguyễn Tuấn Anh, {}'.format(self.tr('Vietnamese'), self.tr('University of Science, Vietnam National University, Hanoi')))
        entry.setFont(font)
        self.groupBoxTranslators.layout().addWidget(entry)
