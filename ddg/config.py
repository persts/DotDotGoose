
import configparser
import os

HOME = os.path.expanduser("~") + "\\AppData\\Local\\DotDotIC\\"

class DDConfig:
    DEFAULTFILE = HOME + "config.ini" 
    DEFAULT_UI = {'grid': {'size': 200, 'color': [255, 255, 255]}, 'point': {'radius': 25, 'color': [255, 255, 0]}}
    DEFAULT_CATEGORIES = ["Resistor", "Capacitor", "Crystal", "Diode", "Inductor", "Integrated Circuit", "Transistor", "Discrete <= 3 Pins", "Discrete > 3 Pins", "Connectors"]
    DEFAULT_AUTOSAVE_TIMEOUT = 5. # min

    def __init__(self, filename=None):
        if not os.path.exists(DDConfig.DEFAULTFILE):
            if not os.path.exists(os.path.dirname(DDConfig.DEFAULTFILE)):
                os.makedirs(os.path.dirname(DDConfig.DEFAULTFILE))
            DDConfig.write_default()

        if filename is None:
            self.load(DDConfig.DEFAULTFILE)
        else:
            self.load(filename)

    @staticmethod
    def write_default():
        config = configparser.ConfigParser()
        config["Categories"] = {"Category{:02d}".format(i):c for i,c in enumerate(DDConfig.DEFAULT_CATEGORIES)}
        config["grid"] = {}
        config["point"] = {}
        config["general"] = {}
        config["grid"]["size"] = str(DDConfig.DEFAULT_UI["grid"]["size"])
        config["grid"]["color"] = ",".join([str(i) for i in DDConfig.DEFAULT_UI["grid"]["color"]])
        config["point"]["radius"] = str(DDConfig.DEFAULT_UI["point"]["radius"])
        config["point"]["color"] = ",".join([str(i) for i in DDConfig.DEFAULT_UI["point"]["color"]])
        config["general"]["autosave"] = str(DDConfig.DEFAULT_AUTOSAVE_TIMEOUT) + " # minutes"
        with open(DDConfig.DEFAULTFILE, "w") as f:
            config.write(f)

    def write(self, filename):
        config = configparser.ConfigParser()
        config["Categories"] = {"Category{:02d}".format(i):c for i,c in enumerate(self.categories)}
        config["grid"] = {}
        config["point"] = {}
        config["general"] = {}
        config["grid"]["size"] = self.ui["grid"]["size"]
        config["grid"]["color"] = ",".join(self.ui["grid"]["color"])
        config["point"]["radius"] = self.ui["point"]["radius"]
        config["point"]["color"] = ",".join(self.ui["point"]["color"])
        config["general"]["autosave"] = self.autosave_timeout
        with open(filename, "w") as f:
            config.write(f)

    def load(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        self.categories = [c.strip() for _, c in config["Categories"].items()]
        self.ui = {}
        self.ui["grid"] = {}
        self.ui["point"] = {}
        self.ui["grid"]["size"] = int(config["grid"]["size"])
        self.ui["grid"]["color"] = [int(i.strip()) for i in config["grid"]["color"].split(",")]
        self.ui["point"]["radius"] = int(config["point"]["radius"])
        self.ui["point"]["color"] = [int(i.strip()) for i in config["point"]["color"].split(",")]
        self.autosave_timeout = float(config["general"]["autosave"].split()[0])

class AutoCompleteFile:
    DEFAULTFILE = HOME + "completion.ini"
    DEFAULT_PACKAGES = ["THT", "SMD", "TO-247", "TO-220", "DO-247", "DO-220", "DPAK", "D²PAK", "H²PAK", "HU3PAK", "DirectFET2 L8", "BGAx", 
                        "BGA-292", "QFP-x", "QFP-100", "LQFP-x", "QFN-x",
                        "DFN-x", "TSSOP-20", "TSSOP-16", "TSSOP-14", "VSSOP-8", "SO-16", "SO-16 wide", 
                        "SO-16 narrow", "SO-14", "SO-8", "SO-5", "SO-4", "SOT-223", "SOT-223-4", "SOT-23", "SOT-23-5", 
                        "SOT-23-6", "SOT-323", "SOT-353",
                        "SOT-363", "SMC", "SMB", "SMA", "SOD-123", "SOD-323", "SOD-523", "SOD-923", "SOD-123FL", "SOD-323FL", "SOD-523FL", "SOD-923FL", 
                        "2520", "1812", "1806", "1210", "1206", "0805", "0603", "0402", "0201",]

    DEFAULT_MANUFACTURERS = ["Altera", "Amphenol", "Analog Devices", "Aptiv", "Avago", "Bourns", "Coilcraft", "Cornel Dubilier", "Diodes Incorporated", "Eaton", 
                            "Elna", "EPCOS", "ERNI", "Faratronic", "Fuji Electric", "Hirose", "Hirschmann", "Infineon", "Isabellenhütte", "JST", "KDS", "Kemet",
                            "Kyocera", "Lelon", "LEM", "Linear Technology", "Littelfuse", "Maxim Integrated", "Melexis", "Microchip", "molex", "Murata", "Nexperia", 
                            "Nichicon", "Nippon Chemi-Con", "NXP", "ON Semiconductor", "Panasonic", "Pulse", "Qualcomm", "Renesas",
                            "Rohm", "Rubycon", "Shindengen", "Shizuki", "Silicon Labs", "STMicroelectronics", "Sumida", "Sumitomo", "Susumu", "Taiwan Semiconductor", 
                            "Taiyo Yuden", "TDK", "TE Connectivity", "Texas Instruments", "United Chemi-Con", "Vishay", "Würth Electronics", "Xilinx"]


    def __init__(self, filename=None):
        if not os.path.exists(AutoCompleteFile.DEFAULTFILE):
            if not os.path.exists(os.path.dirname(AutoCompleteFile.DEFAULTFILE)):
                os.makedirs(os.path.dirname(AutoCompleteFile.DEFAULTFILE))
            AutoCompleteFile.write_default()

        if filename is None:
            self.load(AutoCompleteFile.DEFAULTFILE)
        else:
            self.load(filename)

    def load(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        self.packages = list(set([c.strip() for _, c in config["Packages"].items()]))
        self.manufacturers = list(set([c.strip() for _, c in config["Manufacturers"].items()]))
        self.packages.sort()
        self.manufacturers.sort()

    def update(self, filename=None, packages=[], manufacturers=[]):
        if filename is not None:
            config = configparser.ConfigParser()
            config.read(filename)
            _packages = [c.strip() for _, c in config["Packages"].items()]
            _manufacturers = [c.strip() for _, c in config["Manufacturers"].items()]
            if len(packages) > 0: _packages.extend(packages)
            if len(manufacturers) > 0: _manufacturers.extend(manufacturers)
            self.packages = list(set(_packages))
            self.manufacturers = list(set(_manufacturers))
            self.write(filename)
        else:
            self.packages.extend(packages)
            self.manufacturers.extend(manufacturers)
            self.packages = list(set(self.packages))
            self.manufacturers = list(set(self.manufacturers))
        
        self.packages.sort()
        self.manufacturers.sort()

    def write(self, filename):
        self.packages.sort()
        self.manufacturers.sort()
        config = configparser.ConfigParser()
        config["Packages"] = {"Package{:03d}".format(i):c for i,c in enumerate(self.packages)}
        config["Manufacturers"] = {"Manufacturer{:03d}".format(i):c for i,c in enumerate(self.manufacturers)}
        with open(filename, "w") as f:
            config.write(f)

    @staticmethod
    def write_default():
        config = configparser.ConfigParser()
        config["Packages"] = {"Package{:03d}".format(i):c for i,c in enumerate(AutoCompleteFile.DEFAULT_PACKAGES)}
        config["Manufacturers"] = {"Manufacturer{:03d}".format(i):c for i,c in enumerate(AutoCompleteFile.DEFAULT_MANUFACTURERS)}
        with open(AutoCompleteFile.DEFAULTFILE, "w") as f:
            config.write(f)


