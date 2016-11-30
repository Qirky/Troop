"""
    Client/Sender.py
    ------------------

    Sends messages *to* the TroopServer

"""

import socket

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

    def connect(self, hostname, port=57890):
        """ Connects to the master Troop server and
            start a listening instance on this machine """
        if not self.connected:
            # Connect to remote
            self.hostname = hostname
            self.port     = int(port)
            self.address  = (self.hostname, self.port)
            self.conn = socket.socket()
            self.conn.connect(self.address)
            self.connected = True
        return self

    def __call__(self, *args):
        self.conn.sendall("".join(["<{}>".format(arg) for arg in args]))
        return
