# DotDotGoose
DotDotGoose is a free, open source tool to assist with manually counting objects in images.

![Screen Shot](doc/source/example.png)

*Point data collected with DotDotGoose will be very valuable training and validation data for any future efforts with computer assisted counting*



### Dependencies
DotDotGoose is being developed on Ubuntu 22.04 with the following libraries:

* PyQt6 (6.7.1)
* Pillow (10.3.0)
* Numpy (1.26.4)

## Installation
```bash
git clone https://github.com/persts/DotDotGoose
python3 -m venv ddg-env
source ddg-env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r ./DotDotGoose/requirements.txt
```

## Launching DotDotGoose
```bash
cd DotDotGoose
python3 main.py
```

## Executables

Don't want to install from scratch? [Download DotDotGoose and start counting!](https://biodiversityinformatics.amnh.org/open_source/dotdotgoose/)