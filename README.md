# DotDotGoose
DotDotGoose is a free, open source tool to assist with manually counting objects in images.

![Screen Shot](doc/source/example.png)

*Point data collected with DotDotGoose will be very valuable training and validation data for any future efforts with computer assisted counting*



### Dependencies
DotDotGoose is being developed on Ubuntu 22.04 with the following libraries:

* PyQt6 (6.5.2)
* Pillow (10.0.1)
* Numpy (1.24.3)

## Installation

### Building locally

```bash
git clone https://github.com/persts/DotDotGoose
python3 -m venv ddg-env
source ddg-env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r ./DotDotGoose/requirements.txt
```

### Pre-built executables

Don't want to build from scratch? [Download DotDotGoose and start counting!](https://biodiversityinformatics.amnh.org/open_source/dotdotgoose/)

## Launching DotDotGoose

```bash
cd DotDotGoose
python3 main.py
```
