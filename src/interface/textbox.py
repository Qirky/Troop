from __future__ import absolute_import

from ..utils import *
from ..config import *
from ..message import *
from ..interpreter import *
from ..ot.client import Client as OTClient
from ..ot.text_operation import TextOperation, IncompatibleOperationError

from .peer import *
from .constraints import TextConstraint
from .colour_merge import ColourMerge

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

class ThreadSafeText(Text, OTClient):
    is_refreshing = False
    def __init__(self, root, **options):
        
        # Inheret  from Tk.Text and OT client
        
        Text.__init__(self, root.root, **options)
        OTClient.__init__(self, revision=0)

        self.constraint = TextConstraint(self)

        self.config(undo=True, autoseparators=True, maxundo=50)
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_size = 50

        # If we are blending font colours

        self.merge = ColourMerge(self)

        # Queue for reading messages

        self.queue = queue.Queue()
        self.root = root

        self.padx = 2
        self.pady = 2

        # Define message handlers

        self.handles = {}

        self.add_handle(MSG_CONNECT,            self.handle_connect)
        self.add_handle(MSG_OPERATION,          self.handle_operation)
        self.add_handle(MSG_SET_MARK,           self.handle_set_mark)
        self.add_handle(MSG_SELECT,             self.handle_select)
        self.add_handle(MSG_EVALUATE_BLOCK,     self.handle_evaluate)
        self.add_handle(MSG_EVALUATE_STRING,    self.handle_evaluate_str)
        self.add_handle(MSG_REMOVE,             self.handle_remove)
        self.add_handle(MSG_KILL,               self.handle_kill)
        self.add_handle(MSG_SET_ALL,            self.handle_set_all)
        self.add_handle(MSG_RESET,              self.handle_soft_reset)
        self.add_handle(MSG_REQUEST_ACK,        self.handle_request_ack)
        self.add_handle(MSG_CONSTRAINT,         self.handle_text_constraint)

        # Information about other connected users
        self.peers      = self.root.client.peers
        self.peer_tags  = []

        self.marker     = None
        self.local_peer = None
        
        self.scroll_view  = None
        self.scroll_index = None

        self.configure_font()

        self.char_w = self.font.measure(" ")
        self.char_h = self.font.metrics("linespace")

        # Brackets

        left_b  = list("([{")
        right_b = list(")]}")

        self.left_brackets  = dict(zip(left_b, right_b))
        self.right_brackets = dict(zip(right_b, left_b))

        # Set formatting tags

        for tag_name, kwargs in tag_descriptions.items():

            self.tag_config(tag_name, **kwargs)

        # Create 2 docs - one with chars, one with peer ids

        self.document = ""
        self.peer_tag_doc = ""

        # Begin listening for messages

        self.listen()

    # Operational Transformation
    # ==========================

    # Override OTClient
    def send_operation(self, revision, operation):
        """Should send an operation and its revision number to the server."""
        message = MSG_OPERATION(self.marker.id, operation.ops, revision)
        return self.root.add_to_send_queue(message)

    def apply_operation(self, operation, peer=None, undo=False):
        """Should apply an operation from the server to the current document."""

        if len(operation.ops):

            if len(self.read()) != len(self.peer_tag_doc):

                print("{} {}".format( len(self.read()) , len(self.peer_tag_doc)))
                print("Document length mismatch, please restart the Troop server.")
                return

            if peer is None:

                peer = self.active_peer

            # If other peers have added/deleted chars - transform the undo stack

            if peer != self.marker:

                self.transform_undo_stacks(operation)

            # Apply op

            try:

                new_text = operation(self.read())

            except IncompatibleOperationError as err:

                # Get some debug info

                print("Length of text is {}".format(len(self.read())))
                print("Operation is {}".format(operation.ops))
                print("Length: {}".format(get_operation_size(operation.ops)))

                raise err

            self.set_text(new_text)

            self.insert_peer_id(peer, operation.ops)

            peer.de_select()

            # -- new

            self.refresh()

        return

    def apply_local_operation(self, ops, shift_amount, index=None, undo=False, redo=False):
        """ Applies the operation directly after a keypress """

        # Only apply if the operation is not empty

        if not empty_operation(ops):

            operation = TextOperation(ops)
            text = self.read()

            # Set the active peer to the local marker and apply operation

            self.apply_operation(operation, peer=self.marker, undo=undo)

            # Track operations in the undo stack

            self.add_to_undo_stacks(operation, text, undo, redo)

            # Adjust locations of all peers inc. the local one

            self.adjust_peer_locations(self.marker, ops)

            if index is not None:

                self.marker.move(index)

            else:

                self.marker.shift(shift_amount)

        return

    def insert_peer_id(self, peer, ops):
        """ Applies a text operation to the `peer_tag_doc` which contains information about which character relates to which peers """
        operation = TextOperation(self.get_peer_loc_ops(peer, ops))
        self.peer_tag_doc = operation(self.peer_tag_doc)
        return

    def get_state(self):
        """ Returns the state of the OT mechanism as a string """
        return self.state.__class__.__name__

    def active_peers(self):
        """ Returns a list of peers currently connected """
        return [peer for peer in self.peers.values() if peer.connected]

    def transform(self, op1, op2):
        """ Transforms two TextOperations and adjusts the first for the length of the document"""
        try:
            size = max(get_doc_size(op1.ops), len(self.read()))
            new_op1 = TextOperation(new_operation(*(list(op1.ops) + [size])))
            new_op2 = TextOperation(new_operation(*(list(op2.ops) + [size])))
            return TextOperation.transform(new_op1, new_op2)
        except Exception as e:
            print("Error transforming {} and {}".format(new_op1, new_op2))
            raise e

    def transform_undo_stacks(self, operation):
        """ Transforms operations in the undo_stack so their locations are adjusted after other
            operations are applied to the text """
        if len(self.undo_stack):
            self.undo_stack = [self.transform(action, operation)[0] for action in self.undo_stack if len(action.ops)]
        return

    def add_to_undo_stacks(self, operation, document, undo=False, redo=False):
        """ Adds the inverse of an operation to the undo stack """
        # Keep track of operations for use in undo
        if not undo:
            self.undo_stack = self.undo_stack[-self.max_undo_size:] + [operation.invert(document)]
            if not redo:
                self.redo_stack = []
        else:
            self.redo_stack.append(operation.invert(document))
        return

    def get_undo_operation(self):
        """ Gets the last operation from the undo stack """
        return self.undo_stack.pop()

    def get_redo_operation(self):
        """ Gets the last operation from the undo stack """
        return self.redo_stack.pop()

    # Top-level handling
    # ==================

    def add_handle(self, msg_cls, func):
        """ Associates a received message class with a method or function """
        self.handles[msg_cls.type] = func
        return

    def handle(self, message):
        ''' Passes the message onto the correct handler '''
        return self.handles[message.type](message)

    # Handle methods
    # ==============

    def handle_connect(self, message):
        ''' Prints to the console that new user has connected '''
        if self.marker.id != message['src_id']:

            # If a user has connected before, use that Peer instance

            if message["src_id"] in self.peers:

                self.root.reconnect_user(message['src_id'], message['name'])

            else:

                self.root.add_new_user(message['src_id'], message['name'])

            print("Peer '{}' has joined the session".format(message['name']))

        return

    def handle_request_ack(self, message):
        """ After a new client connects, respond to the server to acknowledge"""
        if message['flag'] == 1:
            self.root.block_messages = True
            self.root.add_to_send_queue(MSG_CONNECT_ACK(self.marker.id))
        elif message['flag'] == 0:
            self.root.block_messages = False
        return

    def handle_operation(self, message, client=False):
        """ Forwards the operation message to the correct handler based on whether it
            was sent by the client or server """

        if client:

            operation = TextOperation(message["operation"])

            # This *sends* the operation to the server using text.send_operation(), it does *not* apply it locally

            self.apply_client(operation)

        else:

            # If we recieve a message from the server with our own id, just need acknowledge it

            if message["src_id"] == self.marker.id:

                self.server_ack()

            else:

                self.active_peer = self.get_peer(message)

                operation = TextOperation(message["operation"])

                # Apply the operation received from the server

                self.apply_server(operation)

                if get_operation_size(message["operation"]) != 0:

                    # If the operation is delete/insert, change the indexes of peers that are based after this one

                    self.adjust_peer_locations(self.active_peer, message["operation"])

                    # Move the peer marker

                    self.active_peer.move(get_operation_index(message["operation"]))

                else:

                    # Still need to update the location

                    self.active_peer.refresh()

                # Return to old view

                self.reset_view()

        return

    def handle_set_mark(self, message):
        """ Updates a peer's location """
        peer = self.get_peer(message)
        peer.move(message["index"])
        return

    def handle_select(self, message):
        """ Update's a peer's selection """
        peer = self.get_peer(message)
        peer.select_set(message["start"], message["end"])
        self.update_colours()
        return

    def handle_evaluate(self, message):
        """ Highlights text based on message contents and evaluates the string found """

        peer = self.get_peer(message)

        string = peer.highlight(message["start"], message["end"])

        self.root.lang.evaluate(string, name=str(peer), colour=peer.bg)

        return

    def handle_evaluate_str(self, message):
        """ Evaluates a string as code """

        peer = self.get_peer(message)

        self.root.lang.evaluate(message["string"], name=str(peer), colour=peer.bg)

        return

    def handle_remove(self, message):
        """ Removes a Peer from the session based on the contents of message """
        peer = self.get_peer(message)
        print("Peer '{!s}' has disconnected".format(peer))
        peer.remove()
        return

    def handle_set_all(self, message):
        ''' Sets the contents of the text box and updates the location of peer markers '''

        self.reset() # inherited from OTClient

        self.document = message["document"]

        self.peer_tag_doc = self.create_peer_tag_doc(message["peer_tag_loc"])

        self.refresh()

        for peer_id, index in message["peer_loc"].items():

            peer_id = int(peer_id)

            if peer_id in self.peers:

                self.peers[peer_id].move(index)

        return

    def handle_soft_reset(self, message):
        """ Sets the revision number to 0 and sets the document contents """
        self.revision = 0
        return self.handle_set_all(message)

    def handle_kill(self, message):
        ''' Cleanly terminates the session '''
        return self.root.freeze_kill(message['string'])

    def handle_text_constraint(self, message):
        """ A new text constrait is set """ # TODO: implement the constraints again
        constraint_id = message["constraint_id"]
        dictator_peer = message["src_id"]

        # Don't update if already using

        if constraint_id != self.constraint:

            if not (constraint_id == 0 and self.constraint.rule is None):

                print("New rule received! Setting mode to '{}'".format(str(self.constraint.get_name(constraint_id)).title()))
            
            self.constraint.set_constraint(constraint_id, dictator_peer)
        
        return


    # Reading and writing to the text box
    # ===================================

    def clear(self):
        """ Deletes the contents of the string """
        return self.delete("1.0", END)

    def set_text(self, string):
        """ Sets the contents of the textbox to string"""
        self.document = string
        # self.refresh()
        return

    def read(self):
        """ Returns the entire contents of the text box as a string """
        return self.document

    def readlines(self):
        """ Returns the entire document as a list in which each element is a line from the text"""
        return self.read().split("\n")

    def get_num_lines(self):
        """ Returns the number of lines in the document """
        return int(self.index('end-1c').split('.')[0])

    # Updating / retrieving info from peers
    # =====================================

    def adjust_peer_locations(self, peer, operation):
        """ When a peer performs an operation, adjust the location of peers following it and update
            the location of peer tags """

        shift = get_operation_size(operation)
        index = get_operation_index(operation)

        peer_index = index - shift

        # Un-comment to debug

        # if peer.get_index_num() != peer_index:

        #     print("{} index: {}, Op index: {}, shift: {} === {} ".format(str(peer), peer.get_index_num(), index, shift, peer_index))

        # print("Peer '{}' applying operation of size '{}' at index '{}'".format(str(peer), shift, index))

        doc_size = len(self.read())

        for other in self.peers.values():

            if other !=  peer:

                other_index = other.get_index_num()

                # Moving whole selections

                if other.has_selection():

                    # If the selections overlap, de-highlight the deleted section

                    if peer.has_selection():

                        other.select_remove(peer.select_start(), peer.select_end())

                    # Shift a selected area

                    other.select_shift(peer_index, shift)

                # If the other peer is *in* this peer's selection, move it

                if peer.has_selection() and peer.select_contains( other_index ):
        
                    other.move(peer.select_start())

                # Adjust the index if it comes after the operating peer index

                elif other_index > peer_index:

                    other.shift(shift)

                # If behind, just redraw (if on screen)

                else:

                    other.refresh()

        self.update_colours()

        return

    def create_peer_tag_doc(self, locations):
        """ Re-creates the document of peer_id markers """
        s = []
        for peer_id, length in locations:
            s.append("{}".format(get_peer_char(peer_id)) * int(length))
        return "".join(s)

    def get_peer_loc_ops(self, peer, ops):
        """ Converts a list of operations on the main document to inserting the peer ID """
        # return [str(peer.id) * len(val) if isinstance(val, str) else val for val in ops]
        return [peer.char * len(val) if isinstance(val, str) else val for val in ops]

    def get_peer(self, message):
        """ Retrieves the Peer instance using the "src_id" of message """

        this_peer = None

        if 'src_id' in message and message['src_id'] != -1:

            try:

                this_peer = self.peers[message['src_id']]

            except KeyError as err:

                self.root.freeze_kill(str(err))

        return this_peer

    def update_colours(self):
        """ Sets the peer tags in the text document """

        processed = []

        # Go through connected peers and colour the text

        for p_id, peer in self.peers.items():

            processed.append(peer.char)

            self.update_peer_tag(p_id)

            peer.refresh_highlight()

        # If there are any other left over peers, keep their colours

        for p_id in set(self.peer_tag_doc):

            if str(p_id) not in processed:

                self.update_peer_tag(get_peer_id_from_char(p_id))

        return

    def update_peer_tag(self, p_id):
        """ Refreshes a peer's text_tag colours """

        text_tag = Peer.get_text_tag(p_id)

        # Make sure we include peers no longer connected

        if text_tag not in self.peer_tags:

            self.peer_tags.append(text_tag)

            fg, _ = PeerFormatting(int(p_id))

            self.tag_config(text_tag, foreground=fg)

        self.tag_remove(text_tag, "1.0", END)

        for start, end in get_peer_locs(get_peer_char(p_id), self.peer_tag_doc):

            self.tag_add(text_tag, self.number_index_to_tcl(start), self.number_index_to_tcl(end))

        return

    # Main loop actions
    # =================

    def put(self, message):
        """ Checks if a message from a new user then writes a network message to the queue """
        assert isinstance(message, MESSAGE)
        self.queue.put(message)
        return

    def listen(self):
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

                    print("Exception occurred in message {!r}: {!r} {!r}".format(self.handles[msg.type].__name__, type(e), e))
                    raise(e)

                # Update any other idle tasks

                self.update_idletasks()

        # Break when the queue is empty
        except queue.Empty:

            pass

        # Recursive call
        self.after(30, self.listen)
        return

    def refresh(self):
        """ Clears the text box and loads the current document state, called after an operation """

        self.is_refreshing = True
        
        # Store the current "view" to re-apply later
        self.store_view()
        
        # Remove all the text and insert new text
        self.clear()
        self.insert("1.0", self.document)

        # Update the  colours and formatting
        self.update_colours()
        self.apply_language_formatting()

        self.is_refreshing = False
        
        return

    def refresh_peer_labels(self):
        ''' Updates the locations of the peers to their marks. Called from line_numbers on repeat '''
        
        for peer_id, peer in self.peers.items():
             
             peer.redraw()
        
        return

    # handling key events

    def apply_language_formatting(self):
         """ Iterates over each line in the text and updates the correct colour / formatting """
         for line,  _ in enumerate(self.readlines()):
             self.colour_line(line + 1)
         return

    def colour_line(self, line):
        """ Embold keywords defined in `Interpreter.py` """

        # Get contents of the line

        start, end = "{}.0".format(line), "{}.end".format(line)

        string = self.get(start, end)

        # Go through the possible tags

        for tag_name, tag_finding_func in self.root.lang.re.items():

            self.tag_remove(tag_name, start, end)

            for match_start, match_end in tag_finding_func(string):

                tag_start = "{}.{}".format(line, match_start)
                tag_end   = "{}.{}".format(line, match_end)

                self.tag_add(tag_name, tag_start, tag_end)

        return

    def highlight_brackets(self, bracket):
        """ Call this with a bracket """

        index = self.marker.get_index_num() - 1
        assert self.read()[index] == bracket

        start = self.find_starting_bracket(index - 1, self.right_brackets[bracket], bracket)

        if start is not None:

            self.tag_add(self.bracket_tag, self.number_index_to_tcl(start))
            self.tag_add(self.bracket_tag, self.number_index_to_tcl(index))

        return

    def find_starting_bracket(self, index, left_bracket, right_bracket):
        """ Finds the opening bracket to the closing bracket at line, column co-ords.
            Returns None if not found. """
        text = self.read()
        nests = 0
        for i in range(index, -1, -1):
            if text[i] == left_bracket:
                if nests > 0:
                    nests -= 1
                else:
                    return i
            elif text[i] == right_bracket:
                nests += 1
        return

    # Housekeeping
    # ============

    def store_view(self):
        """ Store the location of the interface view, i.e. scroll, such that the 
            self.marker.bbox will be the same when self.reset_view() is called """

        # If we are at the top of the screen, and the marker is less than 2/3 down the page, keep at top

        top_row    = self.get_visible_row_top()
        marker_row = self.get_marker_row()
        bottom_row = self.get_visible_row_bottom()

        if top_row == 1:

            if marker_row < (bottom_row * 0.66):

                self.scroll_distance = self.get_num_lines() * -1

                return
    
        # Store the current distance between top row and marker.mark

        self.scroll_distance = top_row - marker_row

        return

    def reset_view(self):
        """ Sets the view to the last position stored"""

        # Move to top

        self.yview('move', 0.0)
        
        # Scroll until the scroll-distance is the same as previous (or the end)

        for n in range(self.get_num_lines()):

            if (self.get_visible_row_top() - self.get_marker_row()) >= self.scroll_distance:

                break

            self.yview('scroll', 1, 'units')

        return

    def get_visible_row_top(self):
        """ Returns the row number of the top-most visible line """
        index = self.index("@0,0")
        return int(index.split(".")[0])

    def get_visible_row_bottom(self):
        """ Returns the row number of the bottom-most visible line """
        index = self.index("@0,{}".format(self.winfo_height()))
        return int(index.split(".")[0])

    def get_marker_row(self):
        index = self.index(self.marker.mark)
        return int(index.split(".")[0])

    def configure_font(self):
        """ Sets up font for the editor """

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

        self.bracket_style = {'borderwidth': 2, 'relief' : 'groove'}
        self.bracket_tag = "tag_open_brackets"
        self.tag_config(self.bracket_tag, **self.bracket_style)

        return

    def tcl_index_to_number(self, index):
        """ Takes a tcl index e.g. '1.0' and returns the single number it represents if the
            text contents were a single list """
        row, col = [int(val) for val in self.index(index).split(".")]
        return sum([len(line) + 1 for line in self.read().split("\n")[:row-1]]) + col


    def number_index_to_tcl(self, number):
        """ Takes an integer number and returns the tcl index in the from 'row.col' """
        if number <= 0:
            return "1.0"
        text = self.read()
        # Count columns until a newline, then reset and add 1 to row
        count = 0; row = 1; col = 0
        for i in range(1, len(text)+1):
            char = text[i-1]
            if char == "\n":
                row += 1
                col = 0
            else:
                col += 1
            if i >= number:
                break
        return "{}.{}".format(row, col)

    def get_num_lines(self):
        return int(self.index(END).split(".")[0]) - 1

    def number_index_to_row_col(self, number):
        """ Takes an integer number and returns the row and column as integers """
        tcl_index = self.number_index_to_tcl(number)
        return tuple(int(x) for x in tcl_index.split("."))

    def get_line_contents(self, line):
        """ Returns the contents of a line specified by an integer """
        return self.get("{}.0".format(line), "{}.end".format(line))

    def get_leading_whitespace(self, line):
        """ Returns the number of spaces that a line starts with, if the line is only whitespace, returns 0"""
        line_contents = self.get_line_contents(line)

        if line_contents.startswith(" ") and len(line_contents.strip()) > 0:

            return len(line_contents) - len(line_contents.lstrip(' '))

        return 0
