"""
    Troop-Server
    ------------

    The Troop Server runs on the local machine by default on port 57890.
    These can be changed when instantiating the TroopServer object:

        TroopServer.__init__(hostname, port)

    The Troop Server is what is currently used to exectute the code. The
    contents of the document is not stored on the server, but *all*
    evaluated code is executed on the server machine. This opens up the
    server machine to potentially malicious Python executions, but a security
    module will be included soon.

    The Troop Server should have FoxDot installed in their Python path and
    SuperCollider running on the local machine.

"""
import sys, os
from src.server import TroopServer

if len(sys.argv) == 1:

    server_side_eval = False    

elif sys.argv[1] in ("-s", "--server"):
    
    server_side_eval = True

elif sys.argv[1] in ("-c", "--client"):

    server_side_eval = False

else:

    sys.exit("Usage: python run-server.py --remote or --local")

if os.path.isfile('server.cfg'):

    args = TroopServer.read_configuration_file('server.cfg')

else:

    args = ()

myServer = TroopServer(*args, local=server_side_eval)
myServer.start()

    
    
