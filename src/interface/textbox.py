from ..config import *
from ..message import *
from Tkinter import *
import tkFont
import Queue


class ThreadSafeText(Text):
    def __init__(self, root, **options):
        Text.__init__(self, root.root, **options)
        self.queue = Queue.Queue()
        self.root = root
        
        # Markers for users, including the current one
        self.marker = None
        self.peers = {}

        # Font
        self.font = tkFont.Font(font=("Consolas", 16), name="Font")
        self.font.configure(**tkFont.nametofont("Font").configure())
        self.configure(font="Font")

        # Tags
        self.tag_config("code", background="Red", foreground="White")
        
        self.update_me()
    
    def update_me(self):
        try:
            while True:

                pkg = self.queue.get_nowait()

                # Identify the src peer
                this_peer = self.peers[pkg['src_id']]

                # A message might contain more than 1 message (message-ception) 

                for msg in pkg.packages():

                    # Handles selection changes

                    if msg['type'] == MSG_SELECT:

                        sel1 = str(msg['start'])
                        sel2 = str(msg['end'])
                            
                        this_peer.select(sel1, sel2)

                        this_peer.move(*[int(val) for val in sel2.split(".")])

                    # Handles keypresses

                    elif msg['type'] == MSG_DELETE:
                        
                        line = int(msg['row'])
                        col  = int(msg['col'])

                        if this_peer.hasSelection():

                            this_peer.deleteSelection()

                        else:

                            index = "{}.{}".format(line, col)

                            self.delete(index)

                        this_peer.move(line, col)

                    elif msg['type'] == MSG_BACKSPACE:

                        line = int(msg['row'])
                        col  = int(msg['col'])

                        if this_peer.hasSelection():

                            this_peer.deleteSelection()

                        else:

                            # Move the cursor left one for a backspace

                            if line > 0 and col > 0:

                                index = "{}.{}".format(line, col-1)

                                self.delete(index)

                                this_peer.move(line, col-1)

                            elif line > 1 and col == 0:

                                index = "{}.end".format(line-1,)

                                self.delete(index)

                                col = int(self.index(index).split('.')[1])

                                this_peer.move(line-1, col)

                    elif msg['type'] == MSG_HIGHLIGHT:

                        this_peer.highlightBlock((int(msg['start_line']), int(msg['end_line'])))

                    elif msg['type'] == MSG_SET_MARK:

                        line = msg['row']
                        col  = msg['col']

                        index = line + "." + col

                        self.mark_set(this_peer.mark, index)
                        this_peer.move(int(line), int(col))                        

                    elif msg['type'] == MSG_INSERT:

                        # Get the character to insert
                        
                        char = str(msg['char'])

                        if len(char) > 0 and this_peer.hasSelection():

                            this_peer.deleteSelection()

                        self.insert(this_peer.mark, char)

                        line, col = (int(i) for i in self.index(this_peer.mark).split('.'))

                        this_peer.move(line, col)

                    elif msg['type'] == MSG_GET_ALL:

                        # Return the contents of the text box

                        text = self.get("1.0", END)[:-1]

                        self.root.push_queue.put((MSG_SET_ALL, text, msg['src_id']))

                    elif msg['type'] == MSG_SET_ALL:

                        # Set the contents of the text box

                        text = msg['text']

                        self.delete("1.0", END)
                        self.insert("1.0", text)
                        self.mark_set(INSERT, "1.0")

                    elif msg['type'] == MSG_REMOVE:

                        # Remove a Peer
                        this_peer.remove()
                        
                        del self.peers[msg['src_id']]
                        
                        print("Peer '{}' has disconnected".format(this_peer))

                # Update any other idle tasks

                self.update_idletasks()

        # Break when the queue is empty
        except Queue.Empty:
            pass

        # Recursive call
        self.after(100, self.update_me)
        return

