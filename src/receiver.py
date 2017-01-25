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

    def __init__(self, socket):

        self.sock = socket
        self.address = self.sock.getsockname()

        self.thread = Thread(target=self.handle)
        self.thread.daemon = True
        self.running = False

        # Information about other clients

        self.nodes = {}

        # Information about the text widget

        self.ui = None

    def __call__(self, client_id, attr):
        """ Returns the information about a connected client """
        return getattr(self.nodes[client_id], attr, None)

    def get_id(self):
        """ Returns the client_id nunmber for the local client """
        for node_id, node in self.nodes.items():
            if node == self.address:
                return node_id        

    def start(self):
        self.running = True
        self.thread.start()

    def kill(self):
        self.running = False

    def handle(self):
        i = 0
        while self.running:

            try:

                network_msg = NetworkMessage(self.sock.recv(1024))

            except EmptyMessageError:               

                break

            for msg in network_msg:

                # Store information about a newly connected client

                if type(msg) == MSG_CONNECT:

                    self.nodes[msg['src_id']] = Node(*msg)

                    self.update_text(msg)

                # Code feedback from the server

                elif type(msg) == MSG_RESPONSE:

                    self.ui.console.write(msg['string'])

                # Write the data to the IDE

                else:

                    self.update_text(msg)
                    
        return

    def update_text(self, message):
        ''' Add a Troop message to the Queue '''
        while self.ui is None:
            sleep(0.1)
        self.ui.write(message)
        return
 
class Node:
    """ Class for basic information on other nodes within the network.
    """
    attributes = ('id_num', 'name', 'hostname', 'port', 'row', 'col')
    def __init__(self, id_num, name, hostname, port, row, col):
        self.id       = int(id_num)
        self.name     = name
        self.hostname = hostname
        self.port     = int(port)
        self.address  = (self.hostname, self.port)
        self.row = row
        self.col = col
    def __repr__(self):
        return "{}: {}".format(self.hostname, self.port)        
    def __eq__(self, other):
        return self.address == other
    def __ne__(self, other):
        return self.address != other
        





        
