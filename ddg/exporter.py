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
import numpy as np

from PIL import Image
from PyQt6 import QtCore


class Exporter(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)

    def __init__(self, survey_id, classes, points, working_directory, output_directory, width, height, file_type):
        QtCore.QThread.__init__(self)
        self.survey_id = survey_id
        self.classes = classes
        self.points = points
        self.working_directory = working_directory
        self.output_directory = output_directory
        self.x_offset = width // 2
        self.y_offset = height // 2
        self.file_type = file_type

        self.totals = {}
        for class_name in classes:
            self.totals[class_name] = 0

    def run(self):
        for class_name in self.classes:
            os.makedirs('{}{}{}'.format(self.output_directory, os.path.sep, class_name))
        summary_file_name = '{}{}summary.csv'.format(self.output_directory, os.path.sep)
        summary_file = open(summary_file_name, 'w')
        output = self.tr('survey id,image,class,x,y,chip name')
        summary_file.write(output)
        progress = 2
        for image in self.points:
            try:
                file = Image.open('{}{}{}'.format(self.working_directory, os.path.sep, image))
                img = np.array(file)
                file.close()
                for class_name in self.classes:
                    if class_name in self.points[image]:
                        directory = '{}{}{}{}'.format(self.output_directory, os.path.sep, class_name, os.path.sep)
                        for point in self.points[image][class_name]:
                            progress += 1
                            # set up file name and summary entry
                            self.totals[class_name] += 1
                            file_name = '{:010d}{}'.format(self.totals[class_name], self.file_type)
                            chip_name = '{}{}'.format(directory, file_name)
                            output = '\n{},{},{},{},{},{}'.format(self.survey_id, image, class_name, point.x(), point.y(), chip_name)
                            summary_file.write(output)
                            # caculate the clip window
                            x = max(0, int(point.x()) - self.x_offset)
                            y = max(0, int(point.y()) - self.y_offset)
                            x2 = min((int(point.x()) - self.x_offset) + (self.x_offset * 2), img.shape[1])
                            y2 = min((int(point.y()) - self.y_offset) + (self.y_offset * 2), img.shape[0])
                            window = img[y:y2, x:x2]
                            # fill the chip with data and save
                            chip = np.zeros((self.y_offset * 2, self.x_offset * 2, img.shape[2]), img.dtype)
                            chip[0:window.shape[0], 0:window.shape[1]] = window
                            out_image = Image.fromarray(chip)
                            out_image.save(chip_name)
                            out_image.close()

                            self.progress.emit(progress)
            except FileNotFoundError:
                # Update progress regardless of missing file
                # TODO: Write a summary document with missing images
                for class_name in self.classes:
                    if class_name in self.points[image]:
                        for point in self.points[image][class_name]:
                            progress += 1
                            output = '\n{},{},{},{},{},{}'.format(self.survey_id, image, class_name, 0.0, 0.0, 'Image Not Found')
                            summary_file.write(output)
                            self.progress.emit(progress)

        summary_file.close()
