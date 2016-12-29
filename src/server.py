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
import sys
from time import sleep
from getpass import getpass
from hashlib import md5
from threading import Thread
from threadserv import ThreadedServer
from message import *
from interpreter import *

def stdout(s=""):
    """ Forces prints to server-side """
    sys.__stdout__.write(str(s) + "\n")

class TroopServer:
    """
        This the master Server instance. Other peers on the
        network connect to it and send their keypress information
        to the server, which then sends it on to the others
    """
    def __init__(self, hostname=socket.gethostname(), port=57890, local=True):
        
        # Address information
        
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

        # Set a password for the server
        try:

            self.password = md5(getpass("Password (leave blank for no password): "))

        except KeyboardInterrupt:

            sys.exit()

        # Set up a char queue
        self.char_queue = Queue.Queue()
        self.char_queue_thread = Thread(target=self.update_send)
        self.char_queue_thread.daemon = True

        # All console output is rerouted to the clients
        sys.stdout = self

        # This executes code
        if local:
            self.is_evaluating_local = True
            self.lang = Interpreter()
        else:
            self.is_evaluating_local = False
            self.lang = Clock()
        
        self.boot()

    def boot(self):
        self.running = True
        self.server_thread.start()
        self.char_queue_thread.start()
        stdout("Server running @ {} on port {}\n".format(self.ip_addr, self.port))
        return

    def update_send(self):
        """ This continually sends any characters to clients
        """
        # Attach the message with the ID of sender

        while self.running:

            try:

                client_address, msg = self.char_queue.get_nowait()

                msg['src_id'] = self.clients.index(client_address)

                # Update all clients with message

                for client in self.clients:

                    if 'reply' in msg.data:

                        if msg['reply'] == 1:

                            client.send(msg)

                        elif self.clients.index(client) != msg['src_id']:

                            client.send(msg)

                    else:

                        client.send(msg)

            except Queue.Empty:

                sleep(0.01)

        return
        
    def kill(self):
        self.running = False
        self.server.shutdown()
        self.server.server_close()
        self.lang.quit()
        return

    def write(self, string):
        """ Replaces sys.stdout """
        if string != "\n":

            outgoing = MSG_RESPONSE(-1, string)

            for client in self.clients:
                
                client.send(outgoing)
                    
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

        network_msg = NetworkMessage(self.request.recv(1024))

        if network_msg[0]['password'] == self.master.password.hexdigest():

            self.request.send("1")

        else:

            self.request.send("0")

            stdout("Failed login from {}".format(self.client_address[0]))

            return

        # If success, enter loop
        
        while True:

            try:

                network_msg = NetworkMessage(self.request.recv(1024))

            except:

                # Handle the loss of a client

                stdout("Client @ {} has disconnected".format(self.client_address))

                # Get the ID of the dead clienet

                for client in self.master.clients:

                    if client == self.client_address:

                        dead_client = client

                # Remove from list

                self.master.clients.remove(self.client_address)

                # Notify other clients

                for client in self.master.clients:
                    
                    client.send(MSG_REMOVE(dead_client.id))

                break

            for msg in network_msg:

                if isinstance(msg, MSG_CONNECT) and self.client_address not in self.master.clients:

                    # Store information about the new client

                    new_client = Client(self.client_address, len(self.master.clients))                
                    new_client.name = msg['name']
                    new_client.connect(msg['recv_port'])
                    self.master.clients.append(new_client)

                    stdout("New Connection from {}".format(self.client_address))

                    # Update all other connected clients & vice versa

                    msg1 = MSG_CONNECT(new_client.id, new_client.name, new_client.hostname, new_client.dst_port)

                    for client in self.master.clients:

                        # Tell other clients about the new connection

                        client.send(msg1)

                        # Tell the new client about other clients

                        if client != self.client_address:

                            msg2 = MSG_CONNECT(client.id, client.name, client.hostname, client.dst_port)

                            new_client.send(msg2)
                        
                    # Request the contents of Client 1 and update the new client

                    if len(self.master.clients) > 1:

                        self.master.clients[0].send(MSG_GET_ALL(0, new_client.id))

                elif isinstance(msg, MSG_SET_ALL):

                    # Send the client *all* of the current code

                    new_client_id = msg['client_id']

                    for client in self.master.clients:

                        if client.id == new_client_id:

                            client.send( MSG_SET_ALL(0, msg['string'], new_client_id) )

                # If we have an execute message, evaluate

                elif isinstance(msg, MSG_EVALUATE):

                    if self.master.is_evaluating_local:

                        try:

                            response = self.master.lang.evaluate(msg['string'])

                        except Exception as e:

                            stdout(e)

                    else:

                        # send to clients

                        for client in self.master.clients:

                            client.send( MSG_EVALUATE(msg['src_id'], msg['string']) )
                            
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
        self.conn.sendall(str(string))
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
