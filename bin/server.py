"""
    Troop Server
    ------------

    Real-time collaborative Live Coding with FoxDot and SuperCollder.

    Aims:

    v0.1. - Server machine sends messages to SuperCollider only and
            updates all clients IDE's

    v0.2. - All clients send messages to SuperCollider

    v0.3. - All clients send synchronised messages to SuperCollider

"""
try:
    import FoxDot
except ImportError:
    pass

import socket
import SocketServer
from threading import Thread
from message import *


# 'Master' Server
#   Sits on a machine (can be a performer machine) and listens for incoming
#   connections.

class ThreadedServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class TroopServer:
    """
        This the master Server instance. Other peers on the
        network connect to it and send their keypress information
        to the server, which then sends it on to the others
    """
    def __init__(self, hostname=socket.gethostname(), port=57890, boot=True):
        # Addres information
        self.hostname = hostname
        self.port     = port
        self.address  = (self.hostname, self.port)

        # Instance of a SocketServer
        self.server   = ThreadedServer(self.address, Handler)

        # Reference to the thread that is listening for new connections
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.running = False
        
        # List of clients (hostname, ip)
        self.clients     = []

        # Give handler information about this server
        Handler.master = self

        if boot: self.boot()

    def boot(self):
        self.server_thread.start()
        self.running = True
        # Connect the local peer to this server
        print "Server running on port {}\n".format(self.port)
        return

    def kill(self):
        self.running = False
        self.server.shutdown()
        self.server.server_close()
        return

# Request Handler for TroopServer 

class Handler(SocketServer.BaseRequestHandler):
    master = None
    def handle(self):
        """ self.request = socket
            self.server  = ThreadedServer
            self.client_address = (address, port)
        """
        while self.master.running:

            msg = NetworkMessage(self.request.recv(4096))

            if self.client_address not in self.master.clients:

                print "New Connection from", self.client_address

                new_client = Client(self.client_address, len(self.master.clients))                
                new_client.name = msg[-1]
                new_client.connect(msg[1])

                self.master.clients.append(new_client)

                # Update all other connected clients & vice versa

                msg1 = NetworkMessage.compile("new_client",
                                               new_client.id,
                                               new_client.name,
                                               new_client.hostname,
                                               new_client.dst_port)

                for client in self.master.clients:

                    client.send(msg1)

                    # Don't send information to the new client twice, but it should have a record of itself

                    if client != self.client_address:

                        msg2 = NetworkMessage.compile("new_client",
                                                       client.id,
                                                       client.name,
                                                       client.hostname,
                                                       client.dst_port)

                        new_client.send(msg2)
                    
                # Request the contents of Client 1 and update the new client

                # TODO

            else:

                # Attach the message with the ID of sender

                id_num = self.master.clients.index(self.client_address)

                outgoing = NetworkMessage.compile(id_num, *msg)

                # Update all clients with message

                for client in self.master.clients:

                    if client != self.client_address:

                        client.send(outgoing)

    def notify(self):
        pass

# Keeps information about each connected client

class Client:

    def __init__(self, address, id_num):

        self.hostname = address[0]
        self.src_port = address[1]
        self.address  = address

        self.dst_port = None
        self.dst_addr = None

        self.conn     = None

        # For identification purposes

        self.id = id_num
        self.name = None 
        self.line = 0
        self.column = 0

    def __repr__(self):
        return repr(self.address)

    def send(self, string):
        self.conn.sendall(string)
        return

    def connect(self, port):
        self.dst_port = int(port)
        self.dst_addr = (self.hostname, self.dst_port)
        
        self.conn = socket.socket()
        self.conn.connect(self.dst_addr)
        return self


    def __eq__(self, other):
        return self.address == other
    def __ne__(self, other):
        return self.address != other


if __name__ == "__main__":

    server = TroopServer()

    
