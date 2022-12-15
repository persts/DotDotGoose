# DotDotGoose - Extra Tools

## Export Geographic Coordinates
By default, DotDotGoose stores coordinates in pixel coordinates. If your images are georeferenced you can use the export_geographic.py script to transform the pixel coordinates into geographic coordinates. 

For this script to work your images must be GeoTiffs or tifs, jpgs, pngs with assicated world files (.tfw, .jpg. .pgw respectively).

```bash
[Linux & OSX]
python3 -m venv geo-env
source geo-env/bin/activate
python -m pip install --upgrade pip
python -m pip install rasterio

[Windows]
python -m venv geo-env
geo-env\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install rasterio
```

With your virtual environment activated, simply run the script with 
```
python export_geographic.py
```
and follow the prompts.