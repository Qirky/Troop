"""
    Troop Server
    ------------

    Real-time collaborative Live Coding with FoxDot and SuperCollder.

    Sits on a machine (can be a performer machine) and listens for incoming
    connections and executes FoxDot code.

    Aims:

    v0.1. - Server machine sends messages to SuperCollider only and
            updates all clients IDE's

    v0.2. - All clients send messages to SuperCollider

    v0.3. - All clients send synchronised messages to SuperCollider

"""

import socket
import SocketServer
import Queue
from time import sleep
from getpass import getpass
from hashlib import md5
from threading import Thread
from threadserv import ThreadedServer
from interpreter import *
from message import *

class TroopServer:
    """
        This the master Server instance. Other peers on the
        network connect to it and send their keypress information
        to the server, which then sends it on to the others
    """
    def __init__(self, hostname=socket.gethostname(), port=57890):
        # Addres information
        self.hostname = str(hostname)
        self.ip_addr  = str(socket.gethostbyname_ex(self.hostname)[-1][0])
        self.port     = int(port)

        # Look for an empty port
        port_found = False
        while not port_found:

            try:

                self.server = ThreadedServer((self.hostname, self.port), TroopRequestHandler)
                port_found  = True

            except socket.error:

                self.port += 1

        # Reference to the thread that is listening for new connections
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        
        # List of clients (hostname, ip)
        self.clients     = []

        # Give request handler information about this server
        TroopRequestHandler.master = self

        # This executes code
        self.evaluate = Interpreter()

        # Set a password for the server
        self.password = md5(getpass("Password (leave blank for no password): "))

        # Set up a char queue
        self.char_queue = Queue.Queue()
        self.char_queue_thread = Thread(target=self.update_send)
        self.char_queue_thread.daemon = True

        self.boot()

    def boot(self):
        self.running = True
        self.server_thread.start()
        self.char_queue_thread.start()
        print "Server running @ {} on port {}\n".format(self.ip_addr, self.port)
        return

    def update_send(self):
        """ This continually sends any characters to clients
        """
        # Attach the message with the ID of sender

        while self.running:

            try:

                client_address, msg = self.char_queue.get_nowait()

                id_num = self.clients.index(client_address)

                outgoing = NetworkMessage.compile(msg['type'], id_num, *msg[2:])

                # Update all clients with message

                for client in self.clients:

                    #if client != client_address:

                    client.send(outgoing)

            except Queue.Empty:

                sleep(0.01)

        return
        
    def kill(self):
        self.running = False
        self.server.shutdown()
        self.server.server_close()
        self.evaluate.quit()
        return

# Request Handler for TroopServer 

class TroopRequestHandler(SocketServer.BaseRequestHandler):
    master = None
    def handle(self):
        """ self.request = socket
            self.server  = ThreadedServer
            self.client_address = (address, port)
        """

        # Password test

        msg = NetworkMessage(self.request.recv(1024))

        if msg[-1] == self.master.password.hexdigest():

            self.request.send("1")

        else:

            self.request.send("0")

            print("Failed login from {}".format(self.client_address[0]))

            return

        # If success, enter loop
        
        while True:

            try:

                msg = NetworkMessage(self.request.recv(1024))

            except:

                # Handle the loss of a client

                print "Client @ {} has disconnected".format(self.client_address)

                # Get the ID of the dead clienet

                for client in self.master.clients:

                    if client == self.client_address:

                        dead_client = client

                # Remove from list

                self.master.clients.remove(self.client_address)

                # Notify other clients

                for client in self.master.clients:

                    client.send(NetworkMessage.compile(MSG_REMOVE, dead_client.id))

                break

            if msg.type == MSG_CONNECT and self.client_address not in self.master.clients:

                # Store information about the new client

                new_client = Client(self.client_address, len(self.master.clients))                
                new_client.name = msg[-1]
                new_client.connect(msg[3])
                self.master.clients.append(new_client)

                print("New Connection from", self.client_address)

                # Update all other connected clients & vice versa

                msg1 = NetworkMessage.compile( MSG_CONNECT,
                                               new_client.id,
                                               new_client.name,
                                               new_client.hostname,
                                               new_client.dst_port)

                for client in self.master.clients:

                    # Tell other clients about the new connection

                    client.send(msg1)

                    # Tell the new client about other clients

                    if client != self.client_address:

                        msg2 = NetworkMessage.compile( MSG_CONNECT,
                                                       client.id,
                                                       client.name,
                                                       client.hostname,
                                                       client.dst_port)

                        new_client.send(msg2)
                    
                # Request the contents of Client 1 and update the new client

                if len(self.master.clients) > 1:

                    self.master.clients[0].send(NetworkMessage.compile( MSG_GET_ALL, new_client.id))

            elif msg.type == MSG_SET_ALL:

                # Send the client *all* of the current code

                new_client_id = int(msg[-1])

                for client in self.master.clients:

                    if client.id == new_client_id:

                        client.send(NetworkMessage.compile( MSG_SET_ALL, 0, msg[2] ))

            # If we have an execute message, evaluate

            elif msg.type == MSG_EVALUATE:

                try:

                    response = self.master.evaluate(msg[2])

                    outgoing = NetworkMessage.compile(MSG_RESPONSE, 0, response)

                    for client in self.master.clients:

                        client.send(outgoing)

                except Exception as e:

                    print(e)
                    
            else:

                # Add character to the Queue

                self.master.char_queue.put((self.client_address, msg))
                

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
