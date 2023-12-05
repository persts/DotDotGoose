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


if __name__ == '__main__':
    print("Enter path and image name.")
    print("Example: C:\\data\\mosaic.jpg")
    image_file_name = input('> ')

    print("Enter path and polygon layer.")
    print("Example: C:\\data\\polygons.geojson")
    geojson_file_name = input('> ')

    raster = None
    # image will load geotransform if geotiff or .tfw .jpw .pgw world file present
    try:
        warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)
        raster = rasterio.open(image_file_name)
    except rasterio.errors.RasterioIOError:
        print('Could not open [{}]'.format(image_file_name))
        raster.close()
        sys.exit(0)

    if not check_for_geotransform(raster):
        print('No geotransformation information found.')
        raster.close()
        sys.exit(0)

    geojson = None
    try:
        file = open(geojson_file_name, 'r')
        geojson = json.load(file)
        file.close()
    except FileNotFoundError:
        print('Could not open [{}]'.format(geojson_file_name))
        sys.exit(0)

    # Fake labelme format to pass check
    annotations = {'shapes': [], 'imageData': None}
    for feature in geojson['features']:
        if feature['geometry']['type'] == 'MultiPolygon':
            shape = {'shape_type': 'polygon', 'points': []}
            for point in feature['geometry']['coordinates'][0][0]:
                y, x, = raster.index(point[0], point[1])
                shape['points'].append([x, y])
            annotations['shapes'].append(shape)

    try:
        file_name = os.path.splitext(image_file_name)[0] + '.json'
        file = open(file_name, 'w')
        json.dump(annotations, file)
        file.close()
    except OSError:
        print('Unable to write to [{}]'.format(file_name))
    raster.close()
