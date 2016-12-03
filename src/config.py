import sys

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
