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
import time
import os.path
from datetime import datetime
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
    def __init__(self, hostname=socket.gethostname(), port=57890, local=True, log=False):
          
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
##        if local is True:
##
##            self.is_evaluating_local = True
##            self.lang = Interpreter()
##            sys.stdout = self
##
##        else:
##
##            self.is_evaluating_local = False
##            self.lang = Clock()

        # Set up log for logging a performance

        if log:
            
            # Check if there is a logs folder, if not create it

            log_folder = os.path.join(ROOT_DIR, "logs")

            if not os.path.exists(log_folder):

                os.mkdir(log_folder)

            # Create filename based on date and times
            
            self.fn = time.strftime("server-log-%d%m%y_%H%M%S.txt", time.localtime())
            path    = os.path.join(log_folder, self.fn)
            
            self.log_file   = open(path, "w")
            self.is_logging = True
            
        else:

            self.is_logging = False
            self.log_file = None
        
        # self.boot()

    def start(self):

        self.running = True
        self.server_thread.start()
        self.char_queue_thread.start()

        stdout("Server running @ {} on port {}\n".format(self.ip_addr, self.port))

        while True:

            try:

                sleep(1)

            except KeyboardInterrupt:

                self.kill()

                break
        return

##    def ping_clients(self):
##        ''' Sends a clock-time message to clients '''
##        if self.is_evaluating_local is False:
##            t = self.lang.now()
##            for i, client in enumerate(self.clients):
##                try:
##                    # Get the clock time from the master
##                    if i == 0:
##                        client.send(MSG_GET_TIME())
##                    #else:
##                    #    client.send(MSG_PING())
##                except DeadClientError as err:
##                    self.remove_client(client.address)
##                    stdout(err, "- Client has been removed")
##        return t

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

                except KeyError as err:

                    self.remove_client(client_address)

                    stdout(err)

                # If logging is set to true, store the message info

                if self.is_logging:

                    self.log_file.write("%.4f" % time.clock() + " " + repr(str(msg)) + "\n")

                # If the message is a set_mark message, keep track of that client's row/col

                if type(msg) == MSG_SET_MARK or type(msg) == MSG_INSERT: # How accurate is this??

                    for client in self.clients:

                        if client == client_address:

                            client.row = msg['row']
                            client.col = msg['col']

                            break

                # Update all clients with message

                for client in self.clients:

                    try:

                        if 'reply' in msg.data:

                            if msg['reply'] == 1 or client.id != msg['src_id']:

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

        if client_address in self.clientIDs:
    
            del self.clientIDs[client_address]

        # Notify other clients

        for client in self.clients:
            
            client.send(MSG_REMOVE(dead_client.id))

        return
        
    def kill(self):
        """ Properly terminates the server """
        if self.log_file is not None: self.log_file.close()
        self.running = False
        self.server.shutdown()
        self.server.server_close()
        # self.lang.kill()
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
    bytes  = 4096
    def client_id(self):
        return self.master.clientIDs[self.client_address]
    def handle(self):
        """ self.request = socket
            self.server  = ThreadedServer
            self.client_address = (address, port)
        """

        # Password test

        network_msg = NetworkMessage(self.request.recv(self.bytes))

        if network_msg[0]['password'] == self.master.password.hexdigest():

            # Reply with the client id

            self.master.clientIDs[self.client_address] = self.master.get_next_id()

            self.request.send(str(self.client_id()))

        else:

            # Negative ID indicates failed login

            self.request.send("-1")

            stdout("Failed login from {}".format(self.client_address[0]))

            return

        # If success, enter loop
        
        while True:

            try:

                network_msg = NetworkMessage(self.request.recv(2048))

            except:

                # Handle the loss of a client

                stdout("Client @ {} has disconnected".format(self.client_address))

                self.master.remove_client(self.client_address)

                break

            for msg in network_msg:

                # 1. If we have a new client connecting, add to the address book

                if isinstance(msg, MSG_CONNECT) and self.client_address not in self.master.clients:

                    # Store information about the new client

                    new_client = Client(self.client_address, self.client_id(), self.request)
                    
                    new_client.name = msg['name']

                    self.master.clients.append(new_client)

                    # Print useful info

                    stdout("New Connection from {}".format(self.client_address))

                    # Update all other connected clients & vice versa

                    msg1 = MSG_CONNECT(new_client.id, new_client.name, new_client.hostname, new_client.port)

                    for client in self.master.clients:

                        # Tell other clients about the new connection

                        client.send(msg1)

                        # Tell the new client about other clients

                        if client != self.client_address:

                            msg2 = MSG_CONNECT(client.id, client.name, client.hostname, client.port, client.row, client.col)

                            new_client.send(msg2)
                        
                    # Request the contents of Client 1 and update the new client

                    if len(self.master.clients) > 1:

                        self.master.clients[0].send(MSG_GET_ALL(self.client_id(), new_client.id))

                        # Only get clock time (if necessary) from the first connected client

                        # self.master.clients[0].send(MSG_GET_TIME(self.client_id(), new_client.id))

                    else:

                        # If this is the first client to connect, set clock to 0

                        # self.master.lang.reset() ### TODO is this a good idea?

                        # Set a blank canvas if this is the first to connect

                        self.master.clients[0].send(MSG_SET_ALL(self.master.clients[0].id, "\n\n\n", 0))

                elif isinstance(msg, MSG_SET_ALL):

                    # Send the client *all* of the current code

                    new_client_id = msg['client_id']

                    for client in self.master.clients:

                        if client.id == new_client_id:

                            client.send( MSG_SET_ALL(self.client_id(), msg['string'], new_client_id) )

##                elif isinstance(msg, MSG_SET_TIME):
##
##                    new_client_id = msg['client_id']
##
##                    for client in self.master.clients:
##
##                        if client.id == new_client_id:
##
##                            client.send( MSG_SET_TIME(self.client_id(), msg['time'], msg['timestamp'], new_client_id) )

                # If we have an execute message, evaluate

                # -- may want to have a designated server for making audio? 

                #elif isinstance(msg, MSG_EVALUATE_):
                #    if self.master.is_evaluating_local:
                #        # Evaluate on server
                #        try:
                #            response = self.master.lang.evaluate(msg['string'])
                #        except Exception as e:
                #            stdout(e)
                #    else:
                #        self.master.char_queue.put((self.client_address, msg))
                            
                else:

                    # Add any other messages to the send queue

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
        
        self.row = 0
        self.col = 0

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
