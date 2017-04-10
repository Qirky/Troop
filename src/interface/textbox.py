from ..config import *
from ..message import *
from ..interpreter import *
from Tkinter import *
import tkFont
import Queue
import re

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
            if peer != other and (other.row + 1) >= row >= (other.row - 1):
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

                elif isinstance(msg, MSG_HIGHLIGHT):

                    this_peer.highlightBlock((int(msg['start_line']), int(msg['end_line'])))

                elif isinstance(msg, MSG_SET_MARK):

                    row = str(msg['row'])
                    col = str(msg['col'])

                    index = row + "." + col

                    self.mark_set(this_peer.mark, index)

                    # If this is a local peer, set the insert too

                    if this_peer == self.marker:

                        self.mark_set(INSERT, index)

                        self.see(INSERT)

                    # move the peer to the mark

                    #stdout("setting mark move")
                    
                    #this_peer.move(int(row), int(col))

                    # self.refreshPeerLabels()

                elif type(msg) == MSG_INSERT:

                    self.handle_insert(this_peer, msg['char'], msg['row'], msg['col'])

                    # Update IDE keywords

                    self.root.colour_line(msg['row'])

                elif isinstance(msg, MSG_GET_ALL):

                    # Return the contents of the text box

                    text = self.handle_getall()

                    self.root.push_queue.put( MSG_SET_ALL(-1, text, msg['client_id']) )

                elif type(msg) == MSG_SET_ALL:

                    # Set the contents of the text box

                    self.handle_setall(msg['string'])

                    for _, peer in self.peers.items():

                        peer.move(peer.row, peer.col)
                        self.mark_set(peer.mark, peer.index())

                    for line,  _ in enumerate(self.readlines()[:-1]):

                        self.root.colour_line(line + 1)

                    self.mark_set(INSERT, "1.0")

                elif isinstance(msg, MSG_REMOVE):

                    # Remove a Peer
                    this_peer.remove()
                    
                    del self.peers[msg['src_id']]
                    
                    print("Peer '{}' has disconnected".format(this_peer))

                elif isinstance(msg, MSG_EVALUATE):

                    # Handles code evaluation
                    self.lang.evaluate(msg['string'])

                elif isinstance(msg, MSG_TIME):

                    # Update local clock

                    self.lang.settime(msg['time'])

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

                # Update any other idle tasks

                self.update_idletasks()

                self.refreshPeerLabels()

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
            i = self.index(peer.mark)
            
            row, col = (int(x) for x in i.split("."))

            # Find out if it is close to another peer

            raised = False

            for peer_row, peer_col in loc:

                #if (row == peer_row or row == peer_row + 1) and (col - 2 < peer_col < col + 2):
                if (row <= peer_row <= row + 1) and (col - 4 < peer_col < col + 4):

                    raised = True

                    break

            # Move the peer
            peer.move(row, col, raised)

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

        # print "mark: " + str(self.index(peer.mark)) + ", adding @ " + str(row) + "." + str(col)
        index = str(row) + "." + str(col)

        # Delete a selection if inputting a character
        if len(char) > 0 and peer.hasSelection():
            peer.deleteSelection()

        # Insert character

        # Check if the locations are the same

        # Need to keep track on the server

##        if index != self.index(peer.mark):
##
##            print "src co-ords do not match for", peer
##
##            peer.row = row
##            peer.col = col
##
##            self.mark_set(peer.mark, index)
        
        self.insert(peer.mark, char, peer.text_tag)

        self.refreshPeerLabels()

        #row, col = (int(i) for i in self.index(peer.mark).split('.'))

        # Update label
        #peer.move(row, col)
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
        # Find tags
        i = 0
        tag_ranges = {}
        for n in range(99): # max_clients - TODO: be more elegant about it
            tag = "text_%d" % n
            tag_data = match_tag(tag, data)
            tag_ranges[tag] = match_indices(tag_data)
            i += len(tag_data)

        # Insert the text
        self.delete("1.0", END)
        self.insert("1.0", data[i:])

        # Add tags
        for tag, loc in tag_ranges.items():
            for i in range(0, len(loc), 2):
                self.tag_add(tag, loc[i], loc[i+1])
                
        return

    def sort_indices(self, list_of_indexes):
        return sorted(list_of_indexes, key=lambda index: tuple(int(i) for i in index.split(".")))

def match_tag(tag_name, string):
    re_tag_range = r"(\[('%s')(, ?'\d+\.\d+')+\])" % tag_name
    match = re.search(re_tag_range, string)
    return match.group(0) if match else str()

def match_indices(string):
    return re.findall(r"'(\d+\.+\d+)'", string)
