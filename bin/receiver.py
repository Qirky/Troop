"""
    Client/Receiver.py
    ------------------

    This listens for incoming messages from the TroopServer

"""

import SocketServer, socket
from threading import Thread
from server import ThreadedServer
from message import NetworkMessage

class Receiver:
    """
        Listens for messages from a remote FoxDot Server instance
        and send keystroke data

    """
    def __init__(self, hostname=socket.gethostname(), port=57891, boot=True):
        self.hostname = hostname
        self.port     = int(port)

        # Make sure we find a port
        setting_port = True

        while setting_port:

            try:

                self.server = ThreadedServer((self.hostname, self.port), Handler)
                setting_port = False
                
            except:
                
                self.port += 1

        self.ip_addr = socket.gethostbyname_ex(self.hostname)[-1][0]
        self.address = (self.ip_addr, self.port)

        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.running = False

        self.conn      = None
        self.connected = False

        Handler.master = self

        # Information about other clients

        self.nodes = {}

        # Information about the text widget

        self.ui = None

        if boot: self.boot()

    def __call__(self, client_id, attr):
        """ Returns the information about a connected client """
        return getattr(self.nodes[client_id], attr, None)

    def get_id(self):
        """ Returns the client_id nunmber for the local client """
        for node_id, node in self.nodes.items():
            if node == self.address:
                return node_id        

    def boot(self):
        self.server_thread.start()
        self.running = True

    def quit(self):
        self.running = False       


class Handler(SocketServer.BaseRequestHandler):
    """ Class for handling messages sent to the peers from
        the server and updating the GUI.
    """
    master = None
    def handle(self):
        while self.master.running:

            msg = NetworkMessage(self.request.recv(4096))

            # Store information about a newly connected client

            if msg[0] == "new_client":

                step = Node.attributes + 1 # for "new_client" header

                for n in range(0, len(msg), step):

                    node_id = int(msg[n+1])

                    self.master.nodes[node_id] = Node(*msg[n+1:n+step])

            # Write the data to the IDE

            else:
                
                self.master.ui.write(msg)
 

class Node:
    """ Class for basic information on other nodes within the network.
        Contains no information about code/text.
    """
    attributes = 4
    def __init__(self, id_num, name, hostname, port):
        self.id       = int(id_num)
        self.name     = name
        self.hostname = hostname
        self.port     = int(port)
        self.address  = (self.hostname, self.port)
    def __eq__(self, other):
        return self.address == other
    def __ne__(self, other):
        return self.address != other
        





        
