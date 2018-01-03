#!/usr/bin/env python
"""
    Troop-Client
    ------------
    Real-time collaborative Live Coding.

    - Troop is a real-time collaborative tool that enables group live
      coding within the same document. To run the client application it
      must be able to connect to a running Troop Server instance on
      your network.

    - Using other Live Coding Languages:
    
        Troop is designed to be used with FoxDot (http://foxdot.org) but
        is also configured to work with Tidal Cycles (http://tidalcycles.org).
        You can run this file with the `--mode` flag followed by "tidalcycles"
        to use the Tidal Cycles language. You can also use any other application
        that can accept code commands as strings via the stdin by specifying
        the path of the interpreter application, such as ghci in the case of
        Tidal Cycles, in place of the "tidalcycles" string when using the
        `--mode` flag.

"""
from src.client import Client
from src.config import *
import os.path
import sys

if "--mode" in sys.argv:

    name = sys.argv[ sys.argv.index("--mode") + 1 ] 

    lang = getInterpreter(name)

else:

    lang = FOXDOT
    
if "-p" in sys.argv or "--public" in sys.argv:

    host, port = PUBLIC_SERVER_ADDRESS

elif os.path.isfile('client.cfg'):

    host, port = Client.read_configuration_file('client.cfg')

    """
    You can set a configuration file if you are connecting to the same
    server on repeated occasions. A password should not be stored. The
    file (client.cfg) should look like:

    host=<host_ip>
    port=<port_no>

    """

else:

    host = readin("Troop Server Address", default="localhost")
    port = readin("Port Number", default="57890")

if "--log" in sys.argv or "-l" in sys.argv:

    logging = True

else:

    logging = False
    

name = readin("Enter a name").replace(" ", "_")

try:

    myClient = Client(host, port, name, lang, logging)

except Exception as e:

    input("{}\nPress return to close.".format(e))
