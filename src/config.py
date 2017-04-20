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

# Public server

PUBLIC_SERVER_ADDRESS = ("188.166.144.124", 57890)

# Choose a language:

FOXDOT        = 0
TIDAL         = 1
SUPERCOLLIDER = 2

langnames = { "FoxDot" : FOXDOT,
              "TidalCycles" : TIDAL,
              "SuperCollider" : SUPERCOLLIDER }

