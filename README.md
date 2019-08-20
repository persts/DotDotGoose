# DotDotGoose
DotDotGoose is a free, open source tool to assist with manually counting objects in images.

![Screen Shot](doc/source/example.png)

*Point data collected with DotDotGoose will be very valuable training and validation data for any future efforts with computer assisted counting*



## Installation

### Dependencies
Nenetic is being developed on Ubuntu 18.04 with the following libraries:

* PyQt5 (5.10.1)
* Pillow (5.4.1)
* Numpy (1.15.4)
* TKinter (3.6.7)

Install GUI libraries:

``` bash
sudo apt install python3-pyqt5 python3-tk
```
Install pip3 and install / upgrade dependencies:
```bash
sudo apt install python3-pip
sudo -H pip3 install --upgrade pillow
sudo -H pip3 install numpy
```

#### Windows and OSX
Once Python3 has been installed, you should be able to simply install the three dependencies .

```bash
pip install pillow
pip install numpy
pip install PyQt5
```



## Launching DotDotGoose

```bash
git clone https://github.com/persts/DotDotGoose
cd DotDotGoose
python3 main.py
```

## Executables

Don't want to install from scratch? [Download DotDotGoose and start counting!](https://biodiversityinformatics.amnh.org/open_source/dotdotgoose/)