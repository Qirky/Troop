from ..config import *
from ..message import *
from ..interpreter import *
from peer import PeerFormatting
from Tkinter import *
import tkFont
import Queue
import re

import constraints
constraints = vars(constraints)

class ThreadSafeText(Text):
    def __init__(self, root, **options):
        Text.__init__(self, root.root, **options)
        self.queue = Queue.Queue()
        self.root = root

        self.padx = 2
        self.pady = 2
        
        # Information about other connected users
        self.peers = {}
        self.peer_tags = []

        if SYSTEM == MAC_OS:

            fontfamily = "Monaco"

        elif SYSTEM == WINDOWS:

            fontfamily = "Consolas"

        else:

            fontfamily = "Courier New"

        # Font
        self.font = tkFont.Font(family=fontfamily, size=12, name="Font")
        self.font.configure(**tkFont.nametofont("Font").configure())

        self.font_bold = tkFont.Font(family=fontfamily, size=12, weight="bold", name="BoldFont")
        self.font_bold.configure(**tkFont.nametofont("BoldFont").configure())
        
        self.configure(font="Font")
        
        self.char_w = self.font.measure(" ")
        self.char_h = self.font.metrics("linespace")

        # Tags
        self.tag_config("code", background="Red", foreground="White")
        self.tag_config("tag_bold", font="BoldFont")

        # Code interpreter
        self.lang = self.root.lang
        
        self.update_me()

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
    
    def update_me(self):
        try:
            while True:

                # Pop the message from the queue

                msg = self.queue.get_nowait()

                # Identify the src peer

                if 'src_id' in msg:

                    this_peer = self.peers[msg['src_id']]

                # Handles selection changes

                if isinstance(msg, MSG_SELECT):

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
                    
                    self.lang.evaluate(string, name=str(this_peer), colour=this_peer.bg)

                elif isinstance(msg, MSG_SET_MARK):

                    row = msg['row']
                    col = msg['col']

                    index = "{}.{}".format(row, col)

                    # If the mark has been put onto the last line, add a buffer line to the end

                    last_row = self.root.convert(self.index(END))[0] - 1

##                    if row == last_row:
##
##                        self.insert(END, "\n")

                    self.mark_set(this_peer.mark, index)

                    this_peer.move(row, col) ## this wasn't here before

                    # If this is a local peer, set the insert too

                    if this_peer == self.marker:

                        self.see(self.marker.mark)

                elif type(msg) == MSG_INSERT:

                    self.handle_insert(this_peer, msg['char'], msg['row'], msg['col'])

                    # Update IDE keywords

                    self.root.colour_line(msg['row'])

                    # If the msg is from the local peer, make sure they see their text AND marker

                    if this_peer == self.marker:

                        self.see(self.marker.mark)

                elif isinstance(msg, MSG_GET_ALL):

                    # Return the contents of the text box

                    text = self.handle_getall()

                    self.root.push_queue.put( MSG_SET_ALL(-1, text, msg['client_id']) )

##                    # -- also send update_mark for each peer
##
##                    for peer_id, peer in self.peers.items():
##
##                        self.root.push_queue.put( MSG_SET_MARK(peer_id, peer.row, peer.col, reply = 0) )

                elif type(msg) == MSG_SET_ALL:

                    # Set the contents of the text box

                    self.handle_setall(msg['string'])

                    # Move the peers to their position

                    for _, peer in self.peers.items():
                        
                        peer.move(peer.row, peer.col)

                        self.mark_set(peer.mark, peer.index())

                    # Format the lines

                    for line,  _ in enumerate(self.readlines()[:-1]):

                        self.root.colour_line(line + 1)

                    # Move the local peer to the start

                    self.marker.move(1,0)                    

                elif isinstance(msg, MSG_REMOVE):

                    # Remove a Peer
                    this_peer.remove()
                    
                    del self.peers[msg['src_id']]
                    
                    print("Peer '{}' has disconnected".format(this_peer))

                elif isinstance(msg, MSG_EVALUATE_STRING):

                    # Handles single lines of code evaluation, e.g. "Clock.stop()", that
                    # might be evaluated but not within the text

                    self.lang.evaluate(msg['string'], name=str(this_peer), colour=this_peer.bg)

                elif isinstance(msg, MSG_BRACKET):

                    # Highlight brackets on local client only

                    if this_peer.id == self.local_peer:

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

                # Update any other idle tasks

                self.update_idletasks()

                self.refreshPeerLabels()

                if msg == self.root.wait_msg:
                    self.root.waiting = False
                    self.root.wait_msg = None

        # Break when the queue is empty
        except Queue.Empty:
            pass

        # Recursive call
        self.after(30, self.update_me)
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
            peer.move(row, col, raised)

            # Send message to server with their location?

            # Store location
            loc.append((row, col))
            
        return

    # handling key events

    def handle_delete(self, peer, row, col):
        if peer.hasSelection():
            
            peer.deleteSelection()
            
        else:

            self.delete("{}.{}".format(row, col))
            
        # peer.move(row, col)
        self.refreshPeerLabels()

        return

    def handle_backspace(self, peer, row, col):
        
        if peer.hasSelection():
            
            peer.deleteSelection()

            # Treat as if 1 char was deleted
            
            self.root.last_col += 1

        else:

            # Move the cursor left one for a backspace

            if row > 0 and col > 0:

                index = "{}.{}".format(row, col-1)

                self.delete(index)

                # peer.move(row, col-1)

            elif row > 1 and col == 0:

                index = "{}.end".format(row-1,)

                self.delete(index)

                col = int(self.index(index).split('.')[1])

                # peer.move(row-1, col)

        self.refreshPeerLabels()

        return

    def handle_insert(self, peer, char, row, col):
        ''' Manual character insert for connected peer '''

        index = str(row) + "." + str(col)

        # Delete a selection if inputting a character

        if len(char) > 0 and peer.hasSelection():

            peer.deleteSelection()

        # Insert character
        
        self.insert(peer.mark, char, peer.text_tag)

        self.refreshPeerLabels()
        
        return

    def handle_getall(self):
        """ String starts with the name of text tags and their ranges in brackets """
        
        data = []

        for tag in self.peer_tags:

            # if tag.startswith("text"):

            tag_range = [str(tag)]

            loc = self.tag_ranges(tag)

            if len(loc) > 0:

                for index in loc:

                    tag_range.append(str(index))

                data.append(tag_range)
                
        contents = "".join([str(item) for item in data])

        contents += self.get("1.0", END)[:-1]

        return contents

    def handle_setall(self, data):

        # We get an error here alot -- why?

        # Find tags
        i = 0
        tag_ranges = {}
        for n in range(100): # max_clients - TODO: be more elegant about it
            tag = "text_{}".format(n)
            tag_data = match_tag(tag, data)
            tag_ranges[tag] = match_indices(tag_data)
            i += len(tag_data)

        # Insert the text
        self.delete("1.0", END)
        self.insert("1.0", data[i:])

        # If a text tag is not used by a connected peer, format the colours anyway

        for tag in tag_ranges:

            if tag not in self.peer_tags:

                index = int(tag.split("_")[-1])

                # configure the tag

                colour, _, _ = PeerFormatting(index)

                self.tag_config(tag, foreground=colour)

        # Add tags
        for tag, loc in tag_ranges.items():
            for i in range(0, len(loc), 2):                    
                self.tag_add(tag, loc[i], loc[i+1])
                
        return

    def sort_indices(self, list_of_indexes):
        return sorted(list_of_indexes, key=lambda index: tuple(int(i) for i in index.split(".")))

def match_list(string):
    re_list = r"\[.*?\]"
    match = re.search(re_list, string)
    return eval( match.group(0) ) if match else []

def match_tag(tag_name, string):
    re_tag_range = r"(\[('%s')(, ?'\d+\.\d+')+\])" % tag_name
    match = re.search(re_tag_range, string)
    return match.group(0) if match else str()

def match_indices(string):
    return re.findall(r"'(\d+\.+\d+)'", string)
