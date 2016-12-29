import sys

def stdout(*args):
    """ Forces prints to server-side """
    sys.__stdout__.write(" ".join([str(s) for s in args]) + "\n")

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

# Choose a language:

LANGUAGE      = 0
FOXDOT        = 0
TIDAL         = 1
SUPERCOLLIDER = 2

LANGUAGE = FOXDOT

