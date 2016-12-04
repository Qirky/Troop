"""
    Troop-Client
    ------------
    Real-time collaborative Live Coding.

    - Troop is a real-time collaborative tool that enables group live
      coding within the same document. Currently, code is only executed
      on the server-side (which may be running on the same machine as
      a client) but this may change in future.

    - Using other Live Coding Languages:
    
        Troop is designed to be used with FoxDot (http://foxdot.org) but
        the __call__ method of interpreter.Interpreter can be replaced to
        do other interesting things with the evaluated portions of code.

"""

from src.client import Client

##host = raw_input("Troop server address: ")
##port = raw_input("Port number: ")
##name = raw_input("Enter a name: ")

host, port, name = "Ryan-Laptop", 57890, "Ryan"

myClient = Client(host, port, name)
