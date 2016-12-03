from interface import *
from sender import *
from receiver import *
from message import *
from time import sleep

import sys

class Client:
    def __init__(self, hostname, port, name=None):

        self.hostname = str(hostname)
        self.port     = int(port)
        self.name     = str(name if name is not None else hostname)

        # Try and connect to server

        try:

            self.send = Sender().connect(self.hostname, self.port)
            
        except:
            
            raise(ConnectionError("Could not connect to host '{}'".format( self.hostname ) ) )

        # Set up a receiver
          
        self.recv = Receiver()

        self.address  = (self.recv.hostname, self.recv.port)

        # Set up a user interface

        self.ui = Interface("Troop - {}@{}:{}".format(self.name, self.recv.hostname, self.recv.port))

        # Update the server with some information about this client
        
        self.send(MSG_CONNECT, self.recv.hostname, self.recv.port, self.name)
        
        # Get *this* client's ID - the server may not have processed it yet, so wait:
        
        timeout = 0
        self.id = None

        while self.id == None:

            self.id = self.recv.get_id()

            timeout += 0.1

            sleep(0.1)

            if timeout > 3:

                raise(ConnectionError("Server timed out"))

        # Give the IDE access to push/pull -> their __call__ methods
        # make them act like methods of self.ui
        self.ui.push = self.send
        self.ui.pull = self.recv

        # Let the IDE know the id and name for local client
        self.ui.setMarker(self.id, self.name)

        # Give the receiving server a reference to the user-interface
        self.recv.ui = self.ui
        self.ui.run()
        
