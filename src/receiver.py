"""
    Client/Receiver.py
    ------------------

    This listens for incoming messages from the TroopServer

"""

import SocketServer, socket
from threading import Thread
from threadserv import ThreadedServer
from time import sleep
from message import *
from config import *

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

    def kill(self):
        self.running = False
        self.server.shutdown()
        self.server.server_close()

class Handler(SocketServer.BaseRequestHandler):
    """ Class for handling messages sent to the peers from
        the server and updating the GUI.
    """
    master = None
    def handle(self):
        i = 0
        while self.master.running:

            try:

                network_msg = NetworkMessage(self.request.recv(4096))

            except EmptyMessageError:               

                break

            # Store information about a newly connected client

            for msg in network_msg:

                if isinstance(msg, MSG_CONNECT):

                    self.master.nodes[msg['src_id']] = Node(*msg)

                # Code feedback from the server

                elif isinstance(msg, MSG_RESPONSE):

                    self.master.ui.console.write(msg['string'])

                # Write the data to the IDE

                else:

                    while self.master.ui is None:

                        sleep(0.1)
                    
                    self.master.ui.write(msg)
 

class Node:
    """ Class for basic information on other nodes within the network.
        Contains no information about code/text.
    """
    attributes = ('id_num', 'name', 'hostname', 'port')
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
        





        
