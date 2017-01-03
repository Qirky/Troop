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
        
        # Information about other connected users
        self.peers = {}
        self.peer_tags = []

        # Font
        self.font = tkFont.Font(font=("Consolas", 12), name="Font")
        self.font.configure(**tkFont.nametofont("Font").configure())
        self.configure(font="Font")

        # Tags
        self.tag_config("code", background="Red", foreground="White")

        # Code interpreter
        self.lang = Interpreter()
        
        self.update_me()

    def alone(self, peer):
        """ Returns True if there are no other peers editing the same line """
        # Possible todo -> make sure there's a 1 line gap
        for other in self.peers.values():
            if peer != other and peer.row == other.row:
                return False
        return True
    
    def update_me(self):
        try:
            while True:

                # Pop the message from the queue

                msg = self.queue.get_nowait()

                # Identify the src peer

                this_peer = self.peers[msg['src_id']]

                # Handles selection changes

                if isinstance(msg, MSG_SELECT):

                    sel1 = str(msg['start'])
                    sel2 = str(msg['end'])
                        
                    this_peer.select(sel1, sel2)

                    this_peer.move(*[int(val) for val in sel2.split(".")])

                # Handles keypresses

                elif isinstance(msg, MSG_DELETE):

                    self.handle_delete(this_peer, msg['row'],  msg['col'])

                elif isinstance(msg, MSG_BACKSPACE):

                    self.handle_backspace(this_peer, msg['row'], msg['col'])

                elif isinstance(msg, MSG_HIGHLIGHT):

                    this_peer.highlightBlock((int(msg['start_line']), int(msg['end_line'])))

                elif isinstance(msg, MSG_SET_MARK):

                    line = str(msg['row'])
                    col  = str(msg['col'])

                    index = line + "." + col

                    self.mark_set(this_peer.mark, index)
                    this_peer.move(int(line), int(col))                        

                elif isinstance(msg, MSG_INSERT):

                    self.handle_insert(this_peer, msg['char'], msg['row'], msg['col'])

                elif isinstance(msg, MSG_GET_ALL):

                    # Return the contents of the text box

                    text = self.handle_getall()

                    self.root.push_queue.put( MSG_SET_ALL(-1, text, msg['client_id']) )

                elif isinstance(msg, MSG_SET_ALL):

                    # Set the contents of the text box

                    self.handle_setall(msg['string'])

                    target_peer = self.peers[msg['client_id']]
                    
                    target_peer.move(1,0)

                    self.mark_set(INSERT, "1.0")

                    self.mark_set(target_peer.mark, "1.0")

                elif isinstance(msg, MSG_REMOVE):

                    # Remove a Peer
                    this_peer.remove()
                    
                    # del self.peers[msg['src_id']]
                    
                    print("Peer '{}' has disconnected".format(this_peer))

                elif isinstance(msg, MSG_EVALUATE):

                    # Handles code evaluation
                    self.lang.evaluate(msg['string'])

                elif isinstance(msg, MSG_TIME):

                    # Update local clock

                    self.lang.settime(msg['time'])

                # Update any other idle tasks

                self.update_idletasks()

        # Break when the queue is empty
        except Queue.Empty:
            pass

        # Recursive call
        self.after(100, self.update_me)
        return

    # handling key events

    def handle_delete(self, peer, row, col):
        if peer.hasSelection():
            peer.deleteSelection()
        else:
            index = "{}.{}".format(row, col)
            self.delete(index)
        peer.move(row, col)
        return

    def handle_backspace(self, peer, row, col):
        if peer.hasSelection():
            
            peer.deleteSelection()

        else:

            # Move the cursor left one for a backspace

            if row > 0 and col > 0:

                index = "{}.{}".format(row, col-1)

                self.delete(index)

                peer.move(row, col-1)

            elif row > 1 and col == 0:

                index = "{}.end".format(row-1,)

                self.delete(index)

                col = int(self.index(index).split('.')[1])

                peer.move(row-1, col)

        return

    def handle_insert(self, peer, char, row, col):
        # TODO - Check row / col
        if len(char) > 0 and peer.hasSelection():
            peer.deleteSelection()
        self.insert(peer.mark, char, peer.text_tag)
        row, col = (int(i) for i in self.index(peer.mark).split('.'))
        peer.move(row, col)
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
        for n in range(10): # max_clients
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

def match_tag(tag_name, string):
    re_tag_range = r"(\[('%s')(, ?'\d+\.\d+')+\])" % tag_name
    match = re.search(re_tag_range, string)
    return match.group(0) if match else str()

def match_indices(string):
    return re.findall(r"'(\d+\.+\d+)'", string)
