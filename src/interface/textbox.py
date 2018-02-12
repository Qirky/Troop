from __future__ import absolute_import

from ..config import *
from ..message import *
from ..interpreter import *

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

class ThreadSafeText(Text):
    def __init__(self, root, **options):
        Text.__init__(self, root.root, **options)

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
        
        # Information about other connected users
        self.peers      = {}
        self.peer_tags  = []
        self.marker     = None
        self.local_peer = None

        if SYSTEM == MAC_OS:

            fontfamily = "Monaco"

        elif SYSTEM == WINDOWS:

            fontfamily = "Consolas"

        else:

            fontfamily = "Courier New"

        # Font

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
        
        self.char_w = self.font.measure(" ")
        self.char_h = self.font.metrics("linespace")

        # Flag to only allow connect and set all messages

        self.is_up_to_date = False

        # Set formatting tags
        
        for tag_name, kwargs in tag_descriptions.items():

            self.tag_config(tag_name, **kwargs)

        # Begin listening for messages
        self.handle()

    def write(self, msg):
        """ Writes a network message to the queue """

        # msg must be a Troop message
        assert isinstance(msg, MESSAGE)
        
        # Keep information about new peers

        if 'src_id' in msg:

            sender_id = msg['src_id']

            if sender_id not in self.peers and sender_id != -1:

                # Get peer's current location & name

                name = self.root.pull(sender_id, "name")

                peer = self.peers[sender_id] = Peer(sender_id, self) 

                peer.name.set(name)

                # Create a bar on the graph
                
                peer.graph = self.root.graphs.create_rectangle(0,0,0,0, fill=peer.bg)

        # Add message to queue
        self.queue.put(msg)

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
        return self.get("1.0", END)

    def update_font_colours(self, recur_time=0):
        """ Updates the font colours of all the peers. Set a recur time
            to update reguarly. 
        """
        # Peers
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

    def log_message(self, message):
        """ If logging is turned on, this method writes each message received to file """
        if self.root.is_logging:
            if len(repr(str(msg))) < 1:
                stdout(msg)
            self.root.log_file.write("%.4f" % time.time() + " " + repr(str(msg)) + "\n")
        return
    
    def handle(self):
        """ Continuously reads from the queue of messages read from the server
            and carries out the specified actions. """
        try:
            while True:

                # Pop the message from the queue

                msg = self.queue.get_nowait()

                # Log anything if necesary

                self.log_message(msg)

                # Identify the src peer

                if 'src_id' in msg:

                    if msg['src_id'] == -1:

                        this_peer = None # Server message

                    else:

                        this_peer = self.peers[msg['src_id']]

                # If we are not up-to-date with server, only accept MSG_CONNECT and MSG_SET_ALL

                    if isinstance(msg, MSG_CONNECT):

                        if self.marker.id != msg['src_id']:

                            print("Peer '{}' has joined the session".format(msg['name']))

                    elif type(msg) == MSG_SET_ALL:

                        # Set the contents of the text box

                        self.handle_setall(msg['data'])

                        # Move the peers to their position

                        for _, peer in self.peers.items():
                            
                            peer.move(peer.row, peer.col)

                            # self.mark_set(peer.mark, peer.index())

                        # Format the lines

                        self.format_text()

                        # Move the local peer to the start

                        self.marker.move(1,0)

                        # Flag that we've been update

                        self.is_up_to_date = True

                    elif self.is_up_to_date:

                            # If the server responds with a console message

                            if isinstance(msg, MSG_RESPONSE):

                                if hasattr(self.root, "console"):

                                    self.root.console.write(msg['string']) 

                            # Stop running when server is manually killed                 

                            elif isinstance(msg, MSG_KILL):

                                if hasattr(self.root, "console"):

                                    self.root.console.write(msg['string']) 

                                self.root.push.kill()
                                self.root.pull.kill()

                            # Handles selection changes

                            elif isinstance(msg, MSG_SELECT):

                                sel1 = str(msg['start'])
                                sel2 = str(msg['end'])
                                    
                                this_peer.select(sel1, sel2)

                            # Handles keypresses

                            elif isinstance(msg, MSG_DELETE):

                                self.handle_delete(this_peer, msg['row'],  msg['col'])

                                self.root.colour_line(msg['row'])

                            elif type(msg) == MSG_BACKSPACE:

                                self.handle_backspace(this_peer, msg['row'], msg['col'])

                                self.root.colour_line(msg['row'])

                            elif isinstance(msg, MSG_EVALUATE_BLOCK):

                                lines = (int(msg['start_line']), int(msg['end_line']))

                                this_peer.highlightBlock(lines)

                                # Experimental -- evaluate code based on highlight

                                string = self.get("{}.0".format(lines[0]), "{}.end".format(lines[1]))
                                
                                self.root.lang.evaluate(string, name=str(this_peer), colour=this_peer.bg)

                            elif isinstance(msg, MSG_EVALUATE_STRING):

                                # Handles single lines of code evaluation, e.g. "Clock.stop()", that
                                # might be evaluated but not within the text

                                self.root.lang.evaluate(msg['string'], name=str(this_peer), colour=this_peer.bg)

                            elif isinstance(msg, MSG_SET_MARK):

                                row = msg['row']
                                col = msg['col']

                                this_peer.move(row, col)

                                # If this is a local peer, make sure we can see the marker

                                if this_peer == self.marker:

                                    self.mark_set(INSERT, "{}.{}".format(row, col))

                                    self.see(self.marker.mark)

                            elif isinstance(msg, MSG_INSERT):

                                self.handle_insert(this_peer, msg['char'], msg['row'], msg['col'])

                                # Update IDE keywords

                                self.root.colour_line(msg['row'])

                                # If the msg is from the local peer, make sure they see their text AND marker

                                if this_peer == self.marker:

                                    self.see(self.marker.mark)

                                self.edit_separator()

                            elif isinstance(msg, MSG_GET_ALL):

                                # Return the contents of the text box

                                data = self.handle_getall()

                                reply = MSG_SET_ALL(-1, data, msg['src_id'])

                                self.root.push_queue.put( reply )           

                            elif isinstance(msg, MSG_REMOVE):

                                # Remove a Peer
                                this_peer.remove()
                                
                                del self.peers[msg['src_id']]
                                
                                print("Peer '{}' has disconnected".format(this_peer))                            

                            elif isinstance(msg, MSG_BRACKET):

                                # Highlight brackets on local client only

                                if this_peer.id == self.marker.id:

                                    row1, col1 = msg['row1'], msg['col1']
                                    row2, col2 = msg['row2'], msg['col2']

                                    peer_col = int(self.index(this_peer.mark).split(".")[1])

                                    # If the *actual* mark is a ahead, adjust

                                    col2 = col2 + (peer_col - col2) - 1

                                    self.tag_add("tag_open_brackets", "{}.{}".format(row1, col1), "{}.{}".format(row1, col1 + 1))
                                    self.tag_add("tag_open_brackets", "{}.{}".format(row2, col2), "{}.{}".format(row2, col2 + 1))

                            elif type(msg) == MSG_CONSTRAINT:

                                new_name = msg['name']

                                print("Changing to constraint to '{}'".format(new_name))

                                for name in self.root.creative_constraints:

                                    if name == new_name:

                                        self.root.creative_constraints[name].set(True)
                                        self.root.__constraint__ = constraints[name](msg['src_id'])

                                    else:

                                        self.root.creative_constraints[name].set(False)

                            elif type(msg) == MSG_SYNC:

                                # Set the contents of the text box

                                self.handle_setall(msg['data'])

                                # Move the peers to their position

                                for _, peer in self.peers.items():
                                    
                                    peer.move(peer.row, peer.col)

                                # Format the lines

                                self.format_text()

                            elif type(msg) == MSG_UNDO:

                                self.handle_undo()

                        # Give some useful information about what the message looked like if error

                else:

                    print("Error in text box handling. Message was {}".format(msg.info()))

                    raise e

                # Update any other idle tasks

                self.update_idletasks()

                # This is possible out of date - TODO check

                if msg == self.root.wait_msg:

                    self.root.waiting = False
                    self.root.wait_msg = None
                    self.root.reset_title()

                self.refreshPeerLabels()

        # Break when the queue is empty
        except queue.Empty:
            
            self.refreshPeerLabels()

        # Recursive call
        self.after(30, self.handle)
        return
    
    def refreshPeerLabels(self):
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

    def handle_delete(self, peer, row, col):
        """ Responds to a MSG_DELETE by deleting the character in front of the peer """
        if peer.hasSelection():
            
            peer.deleteSelection()
            
        else:

            self.delete("{}.{}".format(row, col))
            
        # peer.move(row, col)

        return

    def handle_backspace(self, peer, row, col):
        """ Responds to a MSG_BACKSPACE by deleting the character behind the peer """

        # If the peer has selected text, delete that
        
        if peer.hasSelection():
            
            peer.deleteSelection()

            # Treat as if 1 char was deleted

            if peer is self.marker:
            
               self.root.last_col += 1

        else:

            # Move the cursor left one for a backspace

            if row > 0 and col > 0:

                index = "{}.{}".format(row, col-1)

                self.delete(index)

            elif row > 1 and col == 0:

                index = "{}.end".format(row-1,)

                self.delete(index)

                col = int(self.index(index).split('.')[1])

                # peer.move(row-1, col)

        return

    def handle_insert(self, peer, char, row, col):
        ''' Manual character insert for connected peer '''

        index = str(row) + "." + str(col)

        # Delete a selection if inputting a character

        if len(char) > 0 and peer.hasSelection():

            peer.deleteSelection()

        # Insert the character

        self.insert(peer.mark, char, peer.text_tag)
        
        return

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

    def handle_getall(self):
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

    def handle_setall(self, data):
        """ Sets the contents of the text box """

        # unpack the json data

        data = json.loads(data)

        # Insert the text
        
        self.delete("1.0", END)
        self.insert("1.0", data["contents"])

        # If a text tag is not used by a connected peer, format the colours anyway

        self.set_ranges(data["ranges"])

        # Set the marks

        for peer_id, row, col in data["marks"]:
            
            if peer_id in self.peers:

                self.peers[peer_id].row = int(row)
                self.peers[peer_id].col = int(col)

                
        return

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
