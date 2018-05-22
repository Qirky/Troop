from __future__ import absolute_import, print_function

from .interface import *
from .sender import *
from .receiver import *
from .message import *
from .config import *
from .interpreter import *

from time import sleep, time
from getpass import getpass
from hashlib import md5

try:
    import queue
except ImportError:
    import Queue as queue

import sys

class Client:

    version = '0.6'
    
    def __init__(self, hostname="188.166.144.124", port=57890, name=None, lang=FOXDOT, logging=False, ipv6=False):
        
        self.hostname = str(hostname)
        self.port     = int(port)
        self.name     = str(name if name is not None else hostname)
        self.id       = None

        # Try and connect to server

        try:
            
            self.send = Sender().connect(self.hostname, self.port, ipv6, getpass())

            if not self.send.connected:
                
                raise ConnectionError(self.send.error_message())

            else:

                self.id = self.send.conn_id

                print("Password accepted")

                self.send_queue = queue.Queue()
            
        except ConnectionError as e:

            sys.exit(e)

        if self.id is None: # catch -1 error

            print("No ID number assigned by server")

        # Set up a receiver on the connected socket
          
        self.recv = Receiver(self.send.conn)
        self.recv.start()

        self.address  = (self.send.hostname, self.send.port)

        # Choose the language to use

        try:

            if lang in langtypes:

                self.lang = langtypes[lang]()

            else:

                self.lang = Interpreter(lang)

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
                    conf[line[0]] = line[1]
                except:
                    pass
        return conf['host'], int(conf['port'])

    def update_send(self):
        """ Continually polls the queue and sends any messages to the server """
        try:
            while True:
                
                if self.send.connected:
                
                    try:
                        
                        msg = self.send_queue.get_nowait()

                        self.send( msg )

                    except ConnectionError as e:
                        
                        return print(e)
                    
                    self.ui.root.update_idletasks()
                
                else:
                
                    break
        # Break when the queue is empty
        except queue.Empty:
            pass
            
        # Recursive call
        self.ui.root.after(30, self.update_send)
        return
            
