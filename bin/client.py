from interface import *
from sender import *
from receiver import *

class Client:
    def __init__(self, hostname=None, port=None, name=None):

        self.hostname = hostname if hostname is not None else raw_input("Hostname: ")
        self.port     = int( port if port is not None else raw_input("Port Number: "))

        self.name = name if name is not None else raw_input("Name: ")

        if self.name == "":

            self.name = self.hostname

        self.send = Sender().connect(self.hostname, self.port)
        self.recv = Receiver()

        self.address  = (self.recv.hostname, self.recv.port)

        self.ui = Interface("Troop - {}@{}:{}".format(self.name, self.recv.hostname, self.recv.port))

        # Update the server with some information about this client
        self.send(self.recv.hostname, self.recv.port, self.name)
        
        # Get *this* client's ID
        self.id = None
        while self.id == None:
            self.id = self.recv.get_id()

        # Give the IDE access to push/pull
        self.ui.push = self.send
        self.ui.pull = self.recv

        # Let the IDE know the id and name for local client
        self.ui.setMarker(self.id, self.name)

        # Give the receiving server a reference to the user-interface
        self.recv.ui = self.ui
        self.ui.run()
    

if __name__ == "__main__":

    myClient = Client('Ryan-Laptop', 57890, "Ryan")
        
