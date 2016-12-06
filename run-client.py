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
import os.path

if os.path.isfile('client.cfg'):

    host, port, name = Client.read_configuration_file('client.cfg')

    """
    You can set a configuration file if you are connecting to the same
    server on repeated occassions. A password should not be stored. The
    file (client.cfg) should look like:

    host=<host_ip>
    port=<port_no>
    name=<your_name>

    """

else:

    host = raw_input("Troop server address: ")
    port = raw_input("Port number: ")
    name = raw_input("Enter a name: ")

myClient = Client(host, port, name)
