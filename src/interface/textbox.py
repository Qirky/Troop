from __future__ import absolute_import

from ..config import *
from ..message import *
from ..interpreter import *
from ..ot.client import Client as OTClient
from ..ot.text_operation import TextOperation

from .peer import *

try:
    from Tkinter import *
    import tkFont
except ImportError:
    from tkinter import *
    from tkinter import font as tkFont

try:
    import queue
except:
    import Queue as queue

import re
import time
import sys
import json

from . import constraints
constraints = vars(constraints)

class ThreadSafeText(Text, OTClient):
    def __init__(self, root, **options):
        Text.__init__(self, root.root, **options)
        OTClient.__init__(self, revision=0)

        self.operation = TextOperation()

        self.config(undo=True, autoseparators=True, maxundo=50)

        # If we are blending font colours

        self.merge_colour       = None
        self.merge_time         = 0
        self.merge_time_elapsed = 0
        self.merge_recur_time   = 0
        self.merge_weight       = 0

        self.queue = queue.Queue()
        self.root = root

        self.padx = 2
        self.pady = 2

        # Define message handlers

        self.handles = {}
        #self.add_handle(MSG_INSERT,  self.handle_insert)
        #self.add_handle(MSG_DELETE,  self.handle_delete)
        self.add_handle(MSG_OPERATION, self.handle_operation)
        self.add_handle(MSG_SET_ALL,   self.handle_set_all)
        self.add_handle(MSG_GET_ALL,   self.handle_get_all)
        self.add_handle(MSG_CONNECT,   self.handle_connect)
        self.add_handle(MSG_KILL,      self.handle_kill)
        
        # Information about other connected users
        self.peers      = {}
        self.peer_tags  = []
        self.marker     = None
        self.local_peer = None

        self.configure_font()
        
        self.char_w = self.font.measure(" ")
        self.char_h = self.font.metrics("linespace")

        # Set formatting tags
        
        for tag_name, kwargs in tag_descriptions.items():

            self.tag_config(tag_name, **kwargs)

        # Begin listening for messages

        self.document = ""

        self.run()

    # Override OTClient
    def send_operation(self, revision, operation):
        """Should send an operation and its revision number to the server."""

        message = MSG_OPERATION(self.marker.id, operation.ops, revision)
        
        # Operations are sent directly to the server

        return self.root.client.send( message )

    def apply_operation(self, operation):
        """Should apply an operation from the server to the current document."""

        document = operation(self.read())

        self.set_text(document)

        return

    def apply_local_operation(self, ops):
        
        self.apply_operation(TextOperation(ops))
        
        return

    def refresh_contents(self):

        self.set_text(self.document)

        return

    def put(self, msg):
        """ Checks if a message from a new user then writes a network message to the queue """

        # msg must be a Troop message

        assert isinstance(msg, MESSAGE)
        
        # Keep information about new peers -- is this a good place to do it?

        if 'src_id' in msg:

            sender_id = msg['src_id']

            if sender_id not in self.peers and sender_id != -1:

                self.root.add_new_user(sender_id)

        # Add message to queue
        self.queue.put(msg)

        return

    def add_handle(self, msg_cls, func):
        self.handles[msg_cls.type] = func
        return

    def get_state(self):
        return self.state.__class__.__name__

    # Handles
    # =======

    def handle(self, message):
        ''' Passes the message onto the correct handler '''
        return self.handles[message.type](message)

    def handle_connect(self, message):
        ''' Prints to the console that new user has connected '''
        if self.marker.id != message['src_id']:
            print("Peer '{}' has joined the session".format(messsage['name']))  
        return

    def handle_operation(self, message, client=False):

        if client:

            self.apply_client(TextOperation(message["operation"]))

        else:

            # If we recieve a message from the server with our own id, acknowledge

            if message["src_id"] == self.marker.id:

                self.server_ack()

            else:

                self.apply_server(TextOperation(message["operation"]))

        return

    def handle_set_all(self, message):
        ''' Sets the contents of the text box and updates the location of peer markers '''

        # Set the contents of the text box

        self.set_contents(message['data'])

        # Move the peers to their position

        for _, peer in self.peers.items():
            
            peer.move(peer.row, peer.col)

        # Format the lines

        self.format_text()

        # Move the local peer to the start

        self.marker.move(1,0)

        return

    def handle_get_all(self, message):
        ''' Creates a dictionary of data about the text editor and sends it to the server '''
        data = self.get_contents()
        reply = MSG_SET_ALL(-1, data, message['src_id'])
        self.root.add_to_send_queue( reply )
        return

    def handle_kill(self, message):
        ''' Cleanly terminates the session '''
        return self.root.freeze_kill(message['string'])

    def handle_undo(self):
        ''' Override for Ctrl+Z -- Not implemented '''
        try:
            self.edit_undo()
        except TclError:
            pass
        return "break"

    def handle_redo(self):
        ''' Override for Ctrl+Y -- Not currently implmented '''
        try:
            self.edit_redo()
        except TclError:
            pass
        return "break"

    def clear(self):
        return self.delete("1.0", END)

    def get_contents(self):
        """ Returns a dictionary containing with three pieces of information:

        `ranges` - The TK text tags and the spans the cover withinthe text
        `contents` - The text as a string
        `marks` - The locations of the other client markers

        """

        message = {"ranges": {}}

        for tag in self.tag_names(None):

            if tag.startswith("text_"):

                message["ranges"][tag] = []

                ranges = self.tag_ranges(tag)

                for i in range(0, len(ranges), 2):

                    message["ranges"][tag].append( (str(ranges[i]), str(ranges[i+1])) )

        message["contents"] = self.get("1.0", END)[:-1]

        message["marks"] = [(peer_id, peer.row, peer.col) for peer_id, peer in self.peers.items()]

        return message

    def set_contents(self, data):
        """ Sets the contents of the text box """

        # unpack the json data

        data = json.loads(data)

        # Insert the text
        
        self.clear()
        self.insert("1.0", data["contents"])

        # If a text tag is not used by a connected peer, format the colours anyway

        self.set_ranges(data["ranges"])

        # Set the marks

        for peer_id, row, col in data["marks"]:
            
            if peer_id in self.peers:

                self.peers[peer_id].row = int(row)
                self.peers[peer_id].col = int(col)
                
        return

    def set_text(self, string):
        self.clear()
        self.insert("1.0", string)
        return

    def alone(self, peer, row=None):
        """ Returns True if there are no other peers editing the same line +- 1.
            Row can be specified. """
        row = peer.row if row is None else row
        for other in self.peers.values():
            #if peer != other and (other.row + 1) >= row >= (other.row - 1):
            if peer != other and other.row == row:
                return False
        return True

    def readlines(self):
        """ Returns the text in a list of lines. The first row is empty
            to accommodate TKinter's 1-indexing of rows and columns """
        return [""] + self.get("1.0", END).split("\n")[:-1]

    def read(self):
        """ Returns the entire contents of the text box as a string """
        return self.get("1.0", END)[:-1]

    def update_font_colours(self, recur_time=0):
        """ Updates the font colours of all the peers. Set a recur time
            to update reguarly. 
        """

        for peer in self.peers.values():

            peer.update_colours()
            
            peer.configure_tags()
            
            self.root.graphs.itemconfig(peer.graph, fill=peer.bg)

        if recur_time > 0:

            self.merge_time_elapsed += recur_time

            self.merge_weight = min(self.merge_weight + 0.01, 1)

            if self.merge_weight < 1:

                self.after(recur_time, lambda: self.update_font_colours(recur_time = self.merge_recur_time))

        return

    def get_peer_colour_merge_weight(self):
        return self.merge_weight

    def get_peer(self, message):

        this_peer = None

        if 'src_id' in message and message['src_id'] != -1:

            this_peer = self.peers[message['src_id']]

        return this_peer
    
    def run(self):
        """ Continuously reads from the queue of messages read from the server
            and carries out the specified actions. """
        try:
            while True:

                # Pop the message from the queue

                msg = self.queue.get_nowait()

                # Log anything if necesary

                if self.root.is_logging:

                    self.root.log_message(msg)

                # Get the handler method and call

                try:

                    self.handle(msg)

                except Exception as e:

                    print(e)

                # Update any other idle tasks

                self.update_idletasks()

                self.refresh_peer_labels()

        # Break when the queue is empty
        except queue.Empty:
            
            self.refresh_peer_labels()

        # Recursive call
        self.after(30, self.run)
        return
    
    def refresh_peer_labels(self):
        ''' Updates the locations of the peers to their marks'''
        loc = []
        
        for peer in self.peers.values():
            
            # Get the location of a peer

            try:

                i = self.index(peer.mark)

            except TclError as e:

                continue
                
            row, col = (int(x) for x in i.split("."))

            # Find out if it is close to another peer

            raised = False

            for peer_row, peer_col in loc:

                if (row <= peer_row <= row + 1) and (col - 4 < peer_col < col + 4):

                    raised = True

                    break

            # Move the peer

            try:
    
                peer.move(row, col, raised)

            except ValueError:

                pass

            # Store location
            loc.append((row, col))
            
        return

    # handling key events

    def set_ranges(self, data):
        """ Takes a dictionary of tag names and the ranges they cover
            within the text. Sets and formats these ranges """

        for tag, loc in data.items():

            if tag not in self.peer_tags: # non-existent peers

                src_id = int(tag.split("_")[-1])

                # configure the tag

                colour, _ = PeerFormatting(src_id)

                self.tag_config(tag, foreground=colour)
            
            for start, stop in loc:

                self.tag_add(tag, start, stop)

        return

    def change_ranges(self, data):
        """ If resetting data, this updates existing ranges with new data """
        for tag, loc in data.items():
            self.tag_remove(tag, "1.0", END)
            for start, stop in loc:
                self.tag_add(tag, start, stop)
        return

    def move_peers(self, data):
        """ Updates the locations of all the peers based on a list of tuples
            containing peer id's, row, and column """
        for peer_id, row, col in data:
            if peer_id in self.peers:
                self.peers[peer_id].move(row, col)
        return

    def format_text(self):
        """ Iterates over each line in the text and updates the correct colour / formatting """
        for line,  _ in enumerate(self.readlines()[:-1]):
            self.root.colour_line(line + 1)

    def sort_indices(self, list_of_indexes):
        """ Takes a list of Tkinter indices and returns them sorted by location """
        return sorted(list_of_indexes, key=lambda index: tuple(int(i) for i in index.split(".")))

    def configure_font(self):

        if SYSTEM == MAC_OS:

            fontfamily = "Monaco"

        elif SYSTEM == WINDOWS:

            fontfamily = "Consolas"

        else:

            fontfamily = "Courier New"

        self.font_names = []
        
        self.font = tkFont.Font(family=fontfamily, size=12, name="Font")
        self.font.configure(**tkFont.nametofont("Font").configure())
        self.font_names.append("Font")

        self.font_bold = tkFont.Font(family=fontfamily, size=12, weight="bold", name="BoldFont")
        self.font_bold.configure(**tkFont.nametofont("BoldFont").configure())
        self.font_names.append("BoldFont")

        self.font_italic = tkFont.Font(family=fontfamily, size=12, slant="italic", name="ItalicFont")
        self.font_italic.configure(**tkFont.nametofont("ItalicFont").configure())
        self.font_names.append("ItalicFont")
        
        self.configure(font="Font")

        return