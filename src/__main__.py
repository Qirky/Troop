from __future__ import absolute_import
from .config import *

import sys

def run_client():

    from .client import Client

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

    return

def run_server():

    from .server import TroopServer
    
    myServer = TroopServer(log = "--log" in sys.argv)
    
    myServer.start()
    
    return

def warning():
    """ Prints correct usage """
    s = []
    s.append("Usage: troop --flag [options]")
    s.append("")
    s.append("Flags:")
    s.append("  --client             Start Troop in client mode")
    s.append("  --server             Start Troop in server mode")
    s.append("")
    s.append("Options")
    s.append("  --mode <language>    Start Troop with an alternate language")
    s.append("  -p, --public         Connect to the Troop public server")
    print("\n".join(s))
    return


def main():
    args = sys.argv[1:]
    if "--client" in args:
        run_client()
    elif "--server" in args:
        run_server()
    else:
        warning()
    return

if __name__ == "__main__":

    main()