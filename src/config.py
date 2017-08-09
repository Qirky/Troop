import sys
import os.path

def stdout(*args):
    """ Forces prints to server-side """
    sys.__stdout__.write(" ".join([str(s) for s in args]) + "\n")

def readin(prompt=""):
    while True:
        val = raw_input(prompt)
        if val != "":
            return val

# Absolute path of the root e.g. where run-client.py is found

ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")

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
    "tag_string"    : {"font": "ItalicFont"}
    }


# Public server

PUBLIC_SERVER_ADDRESS = ("188.166.144.124", 57890)

# Choose a language

FOXDOT        = 0
TIDAL         = 1
SUPERCOLLIDER = 2

langnames = { "foxdot" : FOXDOT,
              "tidalcycles" : TIDAL,
              "supercollider" : SUPERCOLLIDER }

def getInterpreter(path):
    """ Returns the integer representing the specified interpreter unless
        a custom path is used, which is returned """
    name = path.lower()
    if name in langnames:
        return langnames[name]
    else:
        return path

