"""
    Troop Server
    ------------

    Real-time collaborative Live Coding with FoxDot and SuperCollder.

    Sits on a machine (can be a performer machine) and listens for incoming
    connections and messages and distributes these to other connected peers.

"""

from __future__ import absolute_import

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver

try:
    import queue
except:
    import Queue as queue

import socket
import sys
import time
import os.path
import json

from datetime import datetime
from time import sleep
from getpass import getpass
from hashlib import md5
from threading import Thread

from .threadserv import ThreadedServer
from .message import *
from .interpreter import *
from .config import *
from .ot.server import Server as OTServer, MemoryBackend
from .ot.text_operation import TextOperation

class TroopServer(OTServer):
    """
        This the master Server instance. Other peers on the
        network connect to it and send their keypress information
        to the server, which then sends it on to the others
    """
    bytes  = 2048
    def __init__(self, port=57890, log=False, debug=False):

        OTServer.__init__(self, "", MemoryBackend())
          
        # Address information
        self.hostname = str(socket.gethostname())

        # Listen on any IP
        self.ip_addr  = "0.0.0.0"
        self.port     = int(port)

        # Public ip for server is the first IPv4 address we find, else just show the hostname
        self.ip_pub = self.hostname
        
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                if info[0] == 2:
                    self.ip_pub = info[4][0]
                    break
        except socket.gaierror:
            pass            

        # Look for an empty port
        port_found = False
        
        while not port_found:

            try:

                self.server = ThreadedServer((self.ip_addr, self.port), TroopRequestHandler)
                port_found  = True

            except socket.error:

                self.port += 1

        # Reference to the thread that is listening for new connections
        self.server_thread = Thread(target=self.server.serve_forever)
        
        # Clients (hostname, ip)
        self.clients = []
        # ID numbers
        self.last_id = -1

        # Give request handler information about this server
        TroopRequestHandler.master = self

        # Set a password for the server
        try:

            self.password = md5(getpass("Password (leave blank for no password): ").encode("utf-8"))

        except KeyboardInterrupt:

            sys.exit("Exited")

        # Set up a char queue
        self.msg_queue = queue.Queue()
        self.msg_queue_thread = Thread(target=self.update_send)

        # Stores all the operations that have been made

        self.operation_history = [] 

        self.contents = {"ranges":{}, "document":"", "marks": []}

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

        # Debugging flag

        self.debugging = debug

        if self.debugging:

            from interface.peer import Peer

            self.new_peer = lambda *args, **kwargs: Peer(*args, **kwargs)

    def get_client(self, client_address):
        """ Returns the server-side representation of a client
            using the client address tuple """
        for client in self.clients:
            if client == client_address:
                return client

    def leader(self):
        return self.clients[0]

    def get_contents(self):
        """ Returns a dictionary with three keys: ranges (a list of ranges of each users' text),
            contents (the document as a string), and marks (...) """
        #return self.contents
        return { "ranges"   : self.contents["ranges"],
                 "marks"    : self.contents["marks"] }

    def store_operation(self, message):
        """ Handles a new MSG_OPERATION by updating the document, performing operational transformation
            (if necessary) on it and storing it. """
        try:
            op = self.receive_operation(message["src_id"], message["revision"], TextOperation(message["operation"]))
            message["operation"] = op.ops
        except:
            return False
        # self.operation_history.append(message)
        return True

    def set_contents(self, data):
        """ Updates the document contents, including the location of user text ranges and marks """
        for key, value in data.items():
            self.contents[key] = value
        return

    def start(self):

        self.running = True
        self.server_thread.start()
        self.msg_queue_thread.start()

        stdout("Server running @ {} on port {}\n".format(self.ip_pub, self.port))

        while True:

            try:

                sleep(0.5)

            except KeyboardInterrupt:

                stdout("\nStopping...\n")

                self.kill()

                break
        return

    def get_next_id(self):
        self.last_id += 1
        return self.last_id

    def clear_history(self):
        """ Removes revision history -- potentially a stupid idea """
        self.backend = MemoryBackend()
        return

    @staticmethod
    def read_configuration_file(filename):
        conf = {}
        with open(filename) as f:
            for line in f.readlines():
                line = line.strip().split("=")
                conf[line[0]] = line[1]
        return conf['host'], int(conf['port'])

    def update_send(self):
        """ This continually sends any operations to clients
        """

        while self.running:

            try:

                msg = self.msg_queue.get_nowait()

                # If logging is set to true, store the message info

                if self.is_logging:

                    self.log_file.write("%.4f" % time.clock() + " " + repr(str(msg)) + "\n")

                # Store the response of the messages
                
                if isinstance(msg, MSG_OPERATION):

                    self.store_operation(msg)

                self.respond(msg)

            except queue.Empty:

                sleep(0.01)

        return

    def respond(self, msg):
        """ Update all clients with a message. Only sends back messages to
            a client if the `reply` flag is nonzero. """

        for client in self.clients:

            try:

                # Send to all other clients and the sender if "reply" flag is true

                if (client.id != msg['src_id']) or ('reply' not in msg.data) or (msg['reply'] == 1):

                    client.send(msg)

            except DeadClientError as err:

                # Remove client if no longer contactable

                self.remove_client(client.address)

                stdout(err)

        return

    def remove_client(self, client_address):

        # Get the ID of the dead clienet

        for client in self.clients:

            if client == client_address:

                dead_client = client

                break

        else:

            dead_client = None

        # Remove from list(s)

        if client_address in self.clients:

            self.clients.remove(client_address)

        # Notify other clients

        if dead_client is not None:

            for client in self.clients:
                
                client.send(MSG_REMOVE(dead_client.id))

        return
        
    def kill(self):
        """ Properly terminates the server """
        if self.log_file is not None: self.log_file.close()

        outgoing = MSG_KILL(-1, "Warning: Server manually killed by keyboard interrupt. Please close the application")

        for client in self.clients:

            client.send(outgoing)

        sleep(0.5)
        
        self.running = False
        self.server.shutdown()
        self.server.server_close()
        
        return

    def write(self, string):
        """ Replaces sys.stdout """
        if string != "\n":

            outgoing = MSG_RESPONSE(-1, string)

            for client in self.clients:
                
                client.send(outgoing)
                    
        return

# Request Handler for TroopServer 

class TroopRequestHandler(socketserver.BaseRequestHandler):
    master = None

    def client(self):        
        return self.get_client(self.get_client_id())

    def get_client(self, client_id):
        for client in self.master.clients:
            if client.id == client_id:
                return client
        return

    def get_client_id(self):
        return self.client_id

    def authenticate(self, password):
        
        if password == self.master.password.hexdigest():

            # Reply with the client id

            self.client_id = self.master.get_next_id()

            stdout("New Connection from {}".format(self.client_address[0]))

        else:

            # Negative ID indicates failed login

            stdout("Failed login from {}".format(self.client_address[0]))

            self.client_id = -1

        # Send back the user_id as a 4 digit number

        reply = "{:04d}".format( self.client_id ).encode()

        self.request.send(reply)

        return self.client_id

    def not_authenticated(self):
        return self.authenticate(self.get_message()[0]['password']) < 0

    def get_message(self):
        data = self.request.recv(self.master.bytes) 
        data = self.reader.feed(data)
        return data


    def handle_client_lost(self):
        """ Terminates cleanly """
        stdout("Client @ {} has disconnected".format(self.client_address))
        self.master.remove_client(self.client_address)
        return

    def handle_connect(self, msg):
        """ Stores information about the new client """
        assert isinstance(msg, MSG_CONNECT)
        if self.client_address not in self.master.clients:
            new_client = Client(self.client_address, self.get_client_id(), self.request, name=msg['name'])
            self.connect_clients(new_client) # Contacts other clients
        return new_client

    def handle_set_all(self, msg):
        """ Forwards the SET_ALL message to requesting client and stores
            the data in self.master.contents """
        assert isinstance(msg, MSG_SET_ALL)

        # Always store the last SET_ALL on the server

        self.master.set_contents( msg["data"] )

        new_client_id = msg['client_id']

        if new_client_id != -1:
            
            for client in self.master.clients:
                
                if client.id == new_client_id:

                    client.send( MSG_SET_ALL(self.get_client_id(), self.master.get_contents(), new_client_id) )

                    break
            
        return

    def leader(self):
        """ Returns the peer client that is "leading" """
        return self.master.leader()
    
    def handle(self):
        """ self.request = socket
            self.server  = ThreadedServer
            self.client_address = (address, port)
        """

        # This takes strings read from the socket and returns json objects

        self.reader = NetworkMessageReader()

        # Password test

        if self.not_authenticated():

            return

        # Enter loop
        
        while self.master.running:

            try:

                network_msg = self.get_message()

                # If we get none, just read in again

                if network_msg is None:

                    continue

            except Exception as e: # TODO be more specific

                # Handle the loss of a client

                self.handle_client_lost()

                break

            for msg in network_msg:

                # Some messages need to be handled here

                if isinstance(msg, MSG_CONNECT):

                    # Clear server history

                    self.master.clear_history()

                    # Add the new client

                    new_client = self.handle_connect(msg)

                    # Request the contents of Client lead and update the new client

                    self.update_client()

                elif isinstance(msg, MSG_SET_ALL):

                    # Send the client *all* of the current code

                    # self.handle_set_all(msg)

                    pass

                else:

                    # Add any other messages to the send queue

                    self.master.msg_queue.put(msg)

        return

    def connect_clients(self, new_client):
        """ Update all other connected clients with info on new client & vice versa """

        # Store the client

        self.master.clients.append(new_client)

        # Connect each client

        msg1 = MSG_CONNECT(new_client.id, new_client.name, new_client.hostname, new_client.port)

        for client in self.master.clients:

            # Tell other clients about the new connection

            client.send(msg1)

            # Tell the new client about other clients

            if client != self.client_address:

                msg2 = MSG_CONNECT(client.id, client.name, client.hostname, client.port, client.row_tk(), client.col)

                new_client.send(msg2)

        return

    def update_client(self):
        """ Send all the previous operations to the client to keep it up to date """

        client = self.client()
        client.send(MSG_SET_ALL(-1, self.master.document, -1)) # TODO add information to this e.g. locations and ranges

        return
    
# Keeps information about each connected client

class Client:
    bytes = TroopServer.bytes
    def __init__(self, address, id_num, request_handle, name=""):

        self.hostname = address[0]
        self.port     = address[1]
        self.address  = address
        
        self.source = request_handle

        self.contents = None

        # For identification purposes

        self.id   = id_num
        self.name = name
        
        self.row = 0
        self.col = 0

    def row_tk(self):
        return self.row + 1

    def __repr__(self):
        return repr(self.address)

    def send(self, message):
        try:
            self.source.sendall(message.bytes()) 
        except Exception as e:
            raise DeadClientError(self.hostname)
        return

    def __eq__(self, other):
        return self.address == other
    def __ne__(self, other):
        return self.address != other

