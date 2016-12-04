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

from src.server import TroopServer

myServer = TroopServer()
    
