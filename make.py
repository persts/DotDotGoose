#!/usr/bin/env python3
import os
from glob import glob

NAME = "DotDotIC"
INSTALLER = "pyinstaller"
PROG = "main.py"
ARGS = ["clean", "windowed"]
EXCLUDES = ["pandas", "scipy", "matplotlib", "xlwings", "beautifulsoup4", "sklearn", "tornado", 
            "hook", "setuptools", "site", "tensorflow", "flask", "cx_freeze", "flake8", "hdf5", 
            "h5py", "ipython", "ipython", "jupyter", "selenium", "requests", "pyinstaller"]

ONEFILE = True
NOUPX = True

for f in glob(".\\ddg\\ui\\*.ui"):
    os.system("pyuic5 {} -o {}".format(f, f.replace(".ui", "_ui.py")))

argstr = " " + " ".join(["--{} ".format(a) for a in ARGS])

argstr += " ".join(["--exclude-module " + m for m in EXCLUDES])
argstr += " --name=" + NAME
call = INSTALLER + " " + PROG + argstr
if ONEFILE:
    call += " --onefile"
else:
    call += " --onedir"
if NOUPX:
    call += " --noupx"
print(call)
os.system(call)