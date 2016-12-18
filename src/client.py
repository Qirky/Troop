from interface import *
from sender import *
from receiver import *
from message import *

from time import sleep, time
from getpass import getpass
from hashlib import md5

import sys

class Client:
    def __init__(self, hostname, port, name=None):

        self.hostname = str(hostname)
        self.port     = int(port)
        self.name     = str(name if name is not None else hostname)
        self.id       = None

        # Try and connect to server

        try:
            
            self.send = Sender().connect(self.hostname, self.port, getpass())

            if not self.send.connected:
                
                raise ConnectionError("Login attempt failed")

            else:

                print("Password accepted")
            
        except ConnectionError as e:

            sys.exit(e)

        # Set up a receiver
          
        self.recv = Receiver()

        self.address  = (self.recv.hostname, self.recv.port)

        # Set up a user interface

        self.ui = Interface("Troop - {}@{}:{}".format(self.name, self.recv.hostname, self.recv.port))

        # Send information about this client to the server

        self.send(MSG_CONNECT(-1, self.name, self.recv.hostname, self.recv.port))
     
        # Get *this* client's ID - the server may not have processed it yet, so wait:
        
        self.id = self.get_client_id()

        self.ui.setMarker(self.id, self.name)

        # Give the IDE access to push/pull -> their __call__ methods
        # make them act like methods of self.ui
        self.ui.push = self.send
        self.ui.pull = self.recv

        # Give the receiving server a reference to the user-interface
        self.recv.ui = self.ui
        self.ui.run()

    def get_client_id(self):
        timeout = 0
        while self.id == None:
            self.id = self.recv.get_id()
            timeout += 0.1
            sleep(0.1)
            if timeout > 3:
                raise(ConnectionError("Server timed out"))
        return self.id

    @staticmethod
    def read_configuration_file(filename):
        conf = {}
        with open(filename) as f:
            for line in f.readlines():
                line = line.strip().split("=")
                conf[line[0]] = line[1]
        return conf['host'], int(conf['port']), conf['name']
            
