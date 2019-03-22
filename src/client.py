from __future__ import absolute_import, print_function

from .interface import *
from .sender import *
from .receiver import *
from .message import *
from .config import *
from .interpreter import *

from time import sleep, time
from hashlib import md5

try:
    import queue
except ImportError:
    import Queue as queue

import sys

class Client:

    version = VERSION
    ui   = None
    send = None
    recv = None
    mainloop_started = False
    
    def __init__(self, **kwargs):

        self.is_alive = True

        # Start the UI

        self.input = ConnectionInput(self, **kwargs)
        self.input.start()

    def setup(self, host="", port="", name="", password="", lang=FOXDOT, args="", logging=False, ipv6=False):

        # ConnectionInput(host, port)
        
        self.hostname = str(host)
        self.port     = int(port)
        self.name     = str(name if name is not None else hostname)
        self.args     = args
        self.id       = None

        # Try and connect to server

        try:
            
            self.send = Sender(self).connect(self.hostname, self.port, self.name, ipv6, password)

            if not self.send.connected:
                
                raise ConnectionError(self.send.error_message())

            else:

                self.id = self.send.conn_id

                assert self.id is not None, "No ID number assigned by server"

                self.input.print_message("Password accepted")

                self.send_queue = queue.Queue()

        # Quit with error output if we cannot connect
            
        # except (ConnectionError, ConnectionRefusedError, AssertionError) as e:
        except Exception as e:

            self.input.print_message(e)

            return

        # Clean up the user interface

        self.input.cleanup()

        # Continue with set up
        # Set up a receiver on the connected socket
          
        self.recv = Receiver(self, self.send.conn)
        self.recv.start()

        self.address  = (self.send.hostname, self.send.port)

        # Choose the language to use

        try:

            lang = getInterpreter(lang)

            if lang in langtypes:

                self.lang = langtypes[lang](self.args)

            else:

                self.lang = Interpreter(lang, self.args)

        except ExecutableNotFoundError as e:

            print(e)

            self.lang = DummyInterpreter()

        # Create address book

        self.peers = {}

        # Set up a user interface

        title = "Troop - {}@{}:{}".format(self.name, self.send.hostname, self.send.port)
        self.ui = Interface(self, title, self.lang, logging)
        self.ui.init_local_user(self.id, self.name)

        # Send information about this client to the server

        self.send( MSG_CONNECT(self.id, self.name, self.send.hostname, self.send.port) )

        # Give the recv / send a reference to the user-interface
        self.recv.ui = self.ui
        self.send.ui = self.ui

        self.ui.run()


    @staticmethod
    def read_configuration_file(filename):
        conf = {}
        with open(filename) as f:
            for line in f.readlines():
                try:
                    line = line.strip().split("=")
                    conf[line[0].strip()] = line[1].strip()
                except:
                    pass
        return conf

    def update_send(self):
        """ Continually polls the queue and sends any messages to the server """
        try:
            while self.send.connected:
                
                try:
                    
                    msg = self.send_queue.get_nowait()

                    self.send( msg )

                except ConnectionError as e:
                    
                    return print(e)
                
                self.ui.root.update_idletasks()
                
        # Break when the queue is empty
        except queue.Empty:
            pass
            
        # Recursive call
        self.ui.root.after(30, self.update_send)
        
        return
            
    def kill(self):
        """ Kills the connection sockets and UI correctly """

        self.is_alive = False

        for attr in (self.recv, self.send, self.ui):

            if attr is not None:

                attr.kill()

        return