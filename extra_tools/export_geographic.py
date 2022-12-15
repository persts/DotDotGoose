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
import json
import warnings
import rasterio


def check_for_geotransform(raster):
    identity_matrix = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    if list(raster.transform) == identity_matrix:
        return False
    return True


def export_coordinates(file_name, survey_id, points):
    raster = None
    # base image will load geotransform if geotiff or .tfw .jpw .pgw world file present
    try:
        warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)
        raster = rasterio.open(file_name)
    except rasterio.errors.RasterioIOError:
        print('Could not open [{}]'.format(file_name))
        raster.close()
        sys.exit(0)

    # if no geotransform found try a KML
    if not check_for_geotransform(raster):
        print('Geotransform not found in [{}]'.format(file_name))
        print('**Experimental**')
        print('Trying to location a KML')
        file_name = os.path.splitext(file_name)[0] + '.kml'
        try:
            raster = rasterio.open(file_name)
        except rasterio.errors.RasterioIOError:
            print('No geotransformation information found.')
            raster.close()
            sys.exit(0)

    if not check_for_geotransform(raster):
        print('No geotransformation information found.')
        raster.close()
        sys.exit(0)

    try:
        csv = open(os.path.splitext(file_name)[0] + '_geo.csv', 'w')
        csv.write('survey id,class,x,y')
        gt = raster.transform
        for class_name in points:
            for entry in points[class_name]:
                x, y = rasterio.transform.xy(gt, entry['y'], entry['x'])
                output = '\n{},{},{},{}'.format(survey_id, class_name, x, y)
                csv.write(output)
        csv.close()
    except OSError:
        print('Unable to write to [{}]'.format(file_name))
        sys.exit(0)
    raster.close()


if __name__ == '__main__':
    print("Enter .pnt path and file name.")
    print("Example: C:\\data\\survey_1\\points.pnt")
    file_name = input('> ')

    try:
        file = open(file_name, 'r')
        data = json.load(file)
        file.close()
    except FileNotFoundError:
        print('Could not open [{}]'.format(file_name))
        sys.exit(0)

    survey_id = data['metadata']['survey_id']
    directory = os.path.split(file_name)[0]
    for image in data['points']:
        file_name = os.path.join(directory, image)
        export_coordinates(file_name, survey_id, data['points'][image])
    print('Export complete.')
