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
from config import *

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

        # ID numbers
        self.clientIDs = {}
        self.last_id = -1

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
        
        # Clients (hostname, ip)
        self.clients = []

        # Give request handler information about this server
        TroopRequestHandler.master = self

        # Set a password for the server
        try:

            self.password = md5(getpass("Password (leave blank for no password): "))

        except KeyboardInterrupt:

            sys.exit("Exited")

        # Set up a char queue
        self.char_queue = Queue.Queue()
        self.char_queue_thread = Thread(target=self.update_send)
        self.char_queue_thread.daemon = True

        # This executes code
        if local is True:

            self.is_evaluating_local = True
            self.lang = Interpreter()
            sys.stdout = self

        else:

            self.is_evaluating_local = False
            self.lang = Clock()
        
        # self.boot()

    def start(self):

        self.running = True
        self.server_thread.start()
        self.char_queue_thread.start()

        stdout("Server running @ {} on port {}\n".format(self.ip_addr, self.port))

        while True:

            # Send a message every 1 second with the server time

            try:
                
                self.ping_clients()

                sleep(1)

            except KeyboardInterrupt:

                self.kill()

                break
        return

    def ping_clients(self):
        ''' Sends a clock-time message to clients '''
        if self.is_evaluating_local is False:
            for client in self.clients:
                client.send(MSG_TIME(self.lang.now()))
        return

    def get_next_id(self):
        self.last_id += 1
        return self.last_id

    @staticmethod
    def read_configuration_file(filename):
        conf = {}
        with open(filename) as f:
            for line in f.readlines():
                line = line.strip().split("=")
                conf[line[0]] = line[1]
        return conf['host'], int(conf['port'])

    def update_send(self):
        """ This continually sends any characters to clients
        """
        # Attach the message with the ID of sender

        while self.running:

            try:

                client_address, msg = self.char_queue.get_nowait()

                try:

                    msg['src_id'] = self.clientIDs[client_address]

                except KeyError as e:

                    print e

                # Update all clients with message

                for client in self.clients:

                    try:

                        if 'reply' in msg.data:

                            if msg['reply'] == 1:

                                client.send(msg)

                            elif client.id != msg['src_id']:

                                client.send(msg)

                        else:

                            client.send(msg)

                    except DeadClientError as err:

                        # Remove client if no longer contactable

                        self.remove_client(client.address)

                        stdout(err)

            except Queue.Empty:

                sleep(0.01)

        return

    def remove_client(self, client_address):

        # Get the ID of the dead clienet

        for client in self.clients:

            if client == client_address:

                dead_client = client

        # Remove from list(s)

        if client_address in self.clients:

            self.clients.remove(client_address)

        del self.clientIDs[client_address]

        # Notify other clients

        for client in self.clients:
            
            client.send(MSG_REMOVE(dead_client.id))

        return

        
    def kill(self):
        self.running = False
        self.server.shutdown()
        self.server.server_close()
        self.lang.kill()
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
    def client_id(self):
        return self.master.clientIDs[self.client_address]
    def handle(self):
        """ self.request = socket
            self.server  = ThreadedServer
            self.client_address = (address, port)
        """

        # Password test

        network_msg = NetworkMessage(self.request.recv(1024))

        if network_msg[0]['password'] == self.master.password.hexdigest():

            # Reply with the client id

            self.master.clientIDs[self.client_address] = self.master.get_next_id()

            self.request.send(str(self.client_id()))

        else:

            self.request.send("-1")

            stdout("Failed login from {}".format(self.client_address[0]))

            return

        # If success, enter loop
        
        while True:

            try:

                network_msg = NetworkMessage(self.request.recv(1024))

            except:

                # Handle the loss of a client

                stdout("Client @ {} has disconnected".format(self.client_address))

                self.master.remove_client(self.client_address)

                break

            for msg in network_msg:

                if isinstance(msg, MSG_CONNECT) and self.client_address not in self.master.clients:

                    # Store information about the new client

                    new_client = Client(self.client_address, self.client_id(), self.request)                
                    new_client.name = msg['name']
                    self.master.clients.append(new_client)

                    stdout("New Connection from {}".format(self.client_address))

                    # Update all other connected clients & vice versa

                    msg1 = MSG_CONNECT(new_client.id, new_client.name, new_client.hostname, new_client.port)

                    for client in self.master.clients:

                        # Tell other clients about the new connection

                        client.send(msg1)

                        # Tell the new client about other clients

                        if client != self.client_address:

                            msg2 = MSG_CONNECT(client.id, client.name, client.hostname, client.port)

                            new_client.send(msg2)
                        
                    # Request the contents of Client 1 and update the new client

                    if len(self.master.clients) > 1:

                        self.master.clients[0].send(MSG_GET_ALL(self.client_id(), new_client.id))

                    else:

                        # If this is the first client to connect, set clock to 0

                        self.master.lang.reset()

                elif isinstance(msg, MSG_SET_ALL):

                    # Send the client *all* of the current code

                    new_client_id = msg['client_id']

                    for client in self.master.clients:

                        if client.id == new_client_id:

                            client.send( MSG_SET_ALL(self.client_id(), msg['string'], new_client_id) )

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

                            client.send( MSG_EVALUATE(self.client_id(), msg['string']) )
                            
                else:

                    # Add character to the Queue

                    self.master.char_queue.put((self.client_address, msg))
                    

# Keeps information about each connected client

class Client:

    def __init__(self, address, id_num, request_handle):

        self.hostname = address[0]
        self.port     = address[1]
        self.address  = address
        
        self.source = request_handle

        # For identification purposes

        self.id = id_num
        self.name = None 
        self.line = 0
        self.column = 0

    def __repr__(self):
        return repr(self.address)

    def send(self, string):
        try:
            self.source.send(str(string))
        except:
            raise DeadClientError(self.hostname)
        return

    def __eq__(self, other):
        return self.address == other
    def __ne__(self, other):
        return self.address != other
