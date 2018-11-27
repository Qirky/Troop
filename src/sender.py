"""
    Client/Sender.py
    ------------------

    Sends messages *to* the TroopServer

"""

from __future__ import absolute_import
from .message import *
from .config import *
from .utils import *

import socket
from hashlib import md5

class Sender:
    """
        Sends messages to the Server

    """
    def __init__(self, client):

        self.client = client

        self.hostname = None
        self.port     = None
        self.address  = None
        self.name     = None
        
        self.conn      = None
        self.conn_id   = None
        self.connected = False
        self.connection_errors = {
            ERR_LOGIN_FAIL : "Login attempt failed",
            ERR_MAX_LOGINS : "Failed to connect: Maximum number of users connected. Please try again later.",
            ERR_NAME_TAKEN : "A user with that name has already connected from your location."
        }

        self.ui        = None

    def connect(self, hostname, port=57890, username="", using_ipv6=False, password=""):
        """ Connects to the master Troop server and
            start a listening instance on this machine """
        if not self.connected:

            # Get details of remote
            self.hostname = hostname
            self.port     = int(port)
            self.address  = (self.hostname, self.port)

            self.name     = username

            # Connect to remote

            try:

                if using_ipv6:

                    self.socket_type = socket.AF_INET6

                    self.address = (self.hostname, self.port, 0, 0)
                    
                else:

                    self.socket_type = socket.AF_INET

                self.conn = socket.socket(self.socket_type, socket.SOCK_STREAM)

                self.conn.connect(self.address)

            except Exception as e:

                raise(e)

                raise(ConnectionError("Could not connect to host '{}'".format( self.hostname ) ) )

            # Send the password

            self.conn_msg = MSG_PASSWORD(-1, md5(password.encode("utf-8")).hexdigest(), self.name)

            self.send( self.conn_msg )

            self.conn_id   = int(self.conn.recv(4)) # careful here
            self.connected = bool(self.conn_id >= 0)
            
        return self

    def send(self, message):
        return self.__call__(message)

    def error_message(self):
        return self.connection_errors.get(self.conn_id, "Connected successfully")

    def __call__(self, message):
        """ Send data to the server """
        try:

            self.conn.sendall(message.bytes())

        except Exception as e:

            # Don't raise exceptions if we already killed client

            if self.client.is_alive:
            
                print(e)
            
                raise ConnectionError("Can't connect to server")
        
        return

    def kill(self):
        self.conn.close()
        return