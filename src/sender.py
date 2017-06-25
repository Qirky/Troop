"""
    Client/Sender.py
    ------------------

    Sends messages *to* the TroopServer

"""

import socket
from message import *
from config import *
from hashlib import md5

class Sender:
    """
        Sends messages to the Server

    """
    def __init__(self):
        self.hostname = None
        self.port     = None
        self.address  = None
        
        self.conn      = None
        self.conn_id   = None
        self.connected = False

    def connect(self, hostname, port=57890, password=""):
        """ Connects to the master Troop server and
            start a listening instance on this machine """
        if not self.connected:

            # Get details of remote
            self.hostname = hostname
            self.port     = int(port)
            self.address  = (self.hostname, self.port)

            # Connect to remote

            try:

                self.conn = socket.socket()
                self.conn.connect(self.address)

            except:

                raise(ConnectionError("Could not connect to host '{}'".format( self.hostname ) ) )

            # Send the password
            self.conn.send(str(MSG_PASSWORD(-1, md5(password).hexdigest())))
            self.conn_id   = int(self.conn.recv(1024))
            self.connected = bool(self.conn_id >= 0)
            
        return self

    def __call__(self, message):
        self.conn.sendall(str(message))
        return

    def kill(self):
        self.conn.close()
        return


