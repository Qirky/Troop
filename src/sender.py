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
        Listens for messages from a remote FoxDot Server instance
        and send keystroke data

    """
    def __init__(self):
        self.hostname = None
        self.port     = None
        self.address  = None
        
        self.conn      = None
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
            self.connected = bool(int(self.conn.recv(1024)))
            
        return self

    def __call__(self, message):
        self.conn.sendall(str(message))
        return

    def kill(self):
        self.conn.close()
        return


