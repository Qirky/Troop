import sys
import os, os.path

VERSION = "0.9.5"

# Check for location of Python

if sys.argv[0] == sys.executable: # If this is compiled file, just use python

    PYTHON_EXECUTABLE = "python"

else:

    PYTHON_EXECUTABLE = os.path.basename(sys.executable)


PY_VERSION = sys.version_info[0]

# Any Py2to3

if PY_VERSION == 2:

    input = raw_input
    FileNotFoundError = IOError

# This removed blurry fonts on Windows
try:
    from ctypes import windll
    try:
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
except ImportError:
    pass

# Apparently this  fixes some issues

try:
    import matplotlib
    matplotlib.use('TkAgg')
except ImportError:
    pass


def stdout(*args):
    """ Forces prints to server-side """
    sys.__stdout__.write(" ".join([str(s) for s in args]) + "\n")

def readin(prompt="", default=None):
    other = " ({})".format(default) if default is not None else ""
    while True:
        try:
            val = input("{}{}: ".format(prompt, other))
            if val != "":
                return val
            elif val == "" and default is not None:
                return default
        except (EOFError, SystemExit, KeyboardInterrupt):
            sys.exit()
    return

# Absolute path of the root e.g. where run-client.py is found

ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")
SRC_DIR = os.path.join(os.path.dirname(__file__))


# Check for OS -> mac, linux, win

SYSTEM  = 0
WINDOWS = 0
LINUX   = 1
MAC_OS  = 2

if sys.platform.startswith('darwin'):

    SYSTEM = MAC_OS

elif sys.platform.startswith('win'):

    SYSTEM = WINDOWS

elif sys.platform.startswith('linux'):

    SYSTEM = LINUX

# RegEx and tags

import re

string_regex = re.compile(r"\".*?\"|'.*?'|\".*?$|'.*?$")

tag_descriptions = {
    "code"          : {"background": "Red", "foreground": "White"},
    "tag_bold"      : {"font": "BoldFont"},
    "tag_italic"    : {"font": "ItalicFont"}
    }


# Public server

PUBLIC_SERVER_ADDRESS_IPV4 = ("188.166.144.124", 57890)
PUBLIC_SERVER_ADDRESS_IPV6 = ("fe80::50f3:caff:fece:f499", 57890)

PUBLIC_SERVER_ADDRESS = PUBLIC_SERVER_ADDRESS_IPV4

# Choose a language

DUMMY         = -1
FOXDOT        = 0
TIDAL         = 1
TIDALSTACK    = 2
SUPERCOLLIDER = 3
SONICPI       = 4

langnames = { "foxdot"           : FOXDOT,
              "tidalcycles"      : TIDAL,
              "tidalcyclesstack" : TIDALSTACK,
              "supercollider"    : SUPERCOLLIDER,
              "sonic-pi"         : SONICPI,
              "none"             : DUMMY }

langtitles = { "foxdot"           : "FoxDot",
               "tidalcycles"      : "TidalCycles",
               "supercollider"    : "SuperCollider",
               "tidalcyclesstack" : "TidalCycles (stack)",
               "sonic-pi"         : "Sonic-Pi",
               "none"             : "No Interpreter" }

def getInterpreter(path):
    """ Returns the integer representing the specified interpreter unless
        a custom path is used, which is returned """
    return langnames.get(path.lower(), path)

# Sorting colours

global COLOUR_INFO_FILE
global COLOURS

# to avoid putting CONF_DIR into the namespace -- why?

CONF_DIR = os.path.join(SRC_DIR, "conf")

if not os.path.exists(CONF_DIR):
    os.makedirs(CONF_DIR)

COLOUR_INFO_FILE = os.path.join(CONF_DIR, "colours.txt")

COLOURS = { "Background" : "#272822",
            "Console"    : "#151613",
            "Stats"      : "#151613",
            "Alpha"      : 0.8,
            "Peers"      : [ "#66D9EF",
                             "#F92672",
                             "#ffd549",
                             "#A6E22E",
                             "#ff108f",
                             "#fffd56",
                             "#0589e7",
                             "#c345f5",
                             "#ff411f",
                             "#05cc50" ] }

def LoadColours():
    """ Reads colour information from COLOUR_INFO and updates
        the IDE accordingly. """
    # Read from file
    read = {}
    try:
        with open(COLOUR_INFO_FILE) as f:
            for line in f.readlines():
                attr, colour = [item.strip() for item in line.split("=")]
                read[attr] = colour
    except IOError:
        pass
    # Load into memory
    for key, colour in read.items():
        if key.startswith("Peer"):
            _, i = key.split()
            COLOURS["Peers"][int(i)-1] = colour
        else:
            COLOURS[key] = colour
    return

LoadColours()

def exe_exists(exe):
    if SYSTEM == WINDOWS: 
        exe = "{}.exe".format(exe)
    return any(
        os.access(os.path.join(path, exe), os.X_OK) 
        for path in os.environ["PATH"].split(os.pathsep)
    )

class ExecutableNotFoundError(Exception):
    def __init__(self, executable):
        Exception.__init__(self, "{}: '{}' is not a valid executable".format(self.__class__.__name__, executable))