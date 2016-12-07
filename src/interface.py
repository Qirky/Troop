from config import *
from message import *
from Tkinter import *
import tkFont
import Queue

class Interface:
    def __init__(self, title="Troop"):
        
        self.root=Tk()
        self.root.title(title)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=2)
        self.root.protocol("WM_DELETE_WINDOW", self.kill )

        # Scroll bar
        self.scroll = Scrollbar(self.root)
        self.scroll.grid(row=0, column=1, sticky='nsew')

        # Text box
        self.text=ThreadSafeText(self, bg="black", fg="white", insertbackground="white")
        self.text.grid(row=0, column=0, sticky="nsew")
        self.scroll.config(command=self.text.yview)


        # Key bindings
        
        CtrlKey = "Command" if SYSTEM == MAC_OS else "Control"

        self.text.bind("<Key>",             self.KeyPress)

        self.text.bind("<<Selection>>",     self.Selection)

        self.text.bind("<{}-Return>".format(CtrlKey),  self.Evaluate)

        self.text.bind("<{}-Home>".format(CtrlKey),  self.CtrlHome)

        self.text.bind("<{}-End>".format(CtrlKey),   self.CtrlEnd)

        # Disabled Key bindings (for now)

        for key in "qwertyuiopasdfghjklzxcvbnm":

            self.text.bind("<{}-{}>".format(CtrlKey, key), lambda e: "break")

        # Directional commands

        self.directions = ("Left", "Right", "Up", "Down", "Home", "End")

        # Selection indices
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        # Listener
        self.pull = lambda *x: None

        # Sender
        self.push = lambda *x: None
        self.push_queue = Queue.Queue()

        # Set the window focus
        self.text.focus_set()

        # Continually check for messages to be sent
        self.update_send()
        
    def run(self):
        self.root.mainloop()
        
    def kill(self):
        try:
            self.pull.kill()
            self.push.kill()
        except(Exception) as e:
            print(e)
        self.root.destroy()

    @staticmethod
    def convert(index):
        return (int(value) for value in index.split("."))

    def setMarker(self, id_num, name):
        self.text.marker=Peer(id_num, self.text)
        self.text.marker.name.set(name)
        
    def write(self, msg):
        """ Writes a network message to the queue
        """
        # Keep information about new peers
        sender_id = msg['src_id']
        if sender_id not in self.text.peers:
            self.text.peers[sender_id] = Peer(sender_id, self.text)
            self.text.peers[sender_id].name.set(self.pull(sender_id, "name"))
        # Add message to queue
        self.text.queue.put(msg)
        return

    def update_send(self):
        """ Sends any keypress information to the server
        """
        try:
            while True:
                args = self.push_queue.get_nowait()
                self.push(*args)
        # Break when the queue is empty
        except Queue.Empty:
            pass

        # Recursive call
        self.root.after(50, self.update_send)
        return
    
    def KeyPress(self, event):
        """ 'Pushes' the key-press to the server.
            - Character
            - Line and column number
            - Timestamp (event.time) - not implemented
        """
        row, col = self.text.index(INSERT).split(".")
        row = int(row)
        col = int(col)

        # Set to None if not inserting text

        ret = "break"

        if event.keysym == "Delete":
            self.push_queue.put((MSG_DELETE, row, col))
            col_offset = -1

        elif event.keysym == "BackSpace":
            self.push_queue.put((MSG_BACKSPACE, row, col))

            if col > 0:

                col_offset = -2

            else:

                row_offset = -1

                if row == 1:

                    col_offset = -1

                else:

                    # length of prev line - col
                    prev_line = self.text.index("{}.end".format(row-1)).split(".")
                    col_offset = int(prev_line[1]) - col

        # Handle key board movement

        elif event.keysym in self.directions:

            if event.keysym == "Left":
                if col > 0:
                    col -= 1
                elif row > 1:
                    prev_line = self.text.index("{}.end".format(row-1)).split(".")
                    row = int(prev_line[0])
                    col = int(prev_line[1])

            elif event.keysym == "Right":
                end_col = int(self.text.index("{}.end".format(row)).split(".")[1])          
                if col == end_col:
                    col = 0
                    row += 1
                else:
                    col += 1

            elif event.keysym == "Up":

                if row > 1:
                    row -= 1
                    prev_end_col = int(self.text.index("{}.end".format(row)).split(".")[1])
                    col = min(col, prev_end_col)

            elif event.keysym == "Down":

                row += 1
                next_end_col = int(self.text.index("{}.end".format(row)).split(".")[1])
                col = min(col, next_end_col)

            elif event.keysym == "Home":

                col = 0

            elif event.keysym == "End":

                col = int(self.text.index("{}.end".format(row)).split(".")[1])

            # Add to queue
            self.push_queue.put((MSG_SET_MARK, row, col))

            # Update the actual insert mark
            self.text.mark_set(INSERT, "{}.{}".format(row, col))

        # Inserting a character

        else:
            
            msg_type = MSG_INSERT

            if event.keysym == "Return":
                char = "\n"
                row_offset = 1
                col_offset = -1-col

            elif event.keysym == "Tab":
                char = "    "
                col += len(char)
                
            else:

                char = event.char

                if char == "": ret = None

            # Add to queue to be pushed to server

            self.push_queue.put((msg_type, char, row, col))
            
        return ret

    def Selection(self, event):
        """ Handles selected areas """
        try:
            self.sel_start = self.text.index(SEL_FIRST)
            self.sel_end   = self.text.index(SEL_LAST)
        except:
            self.sel_start = "0.0"
            self.sel_end   = "0.0"
        self.push_queue.put((MSG_SELECT, self.sel_start, self.sel_end))
        return

    def CtrlHome(self, event):
        return "break"

    def CtrlEnd(self, event):
        return "break"

    def currentBlock(self):
        # Get start and end of the buffer
        start, end = "1.0", self.text.index(END)
        lastline   = int(end.split('.')[0]) + 1

        # Indicies of block to execute
        block = [0,0]        
        
        # 1. Get position of cursor
        cur_x, cur_y = self.text.index(INSERT).split(".")
        cur_x, cur_y = int(cur_x), int(cur_y)
        
        # 2. Go through line by line (back) and see what it's value is
        
        for line in range(cur_x, 0, -1):
            if not self.text.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[0] = line

        # 3. Iterate forwards until we get two \n\n or index==END
        for line in range(cur_x, lastline):
            if not self.text.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[1] = line

        return block

    def Evaluate(self, event):
        # 1. Get the block of code
        lines = self.currentBlock()
        # 2. Send as string to the server
        a, b = ("%d.0" % n for n in lines)
        string = self.text.get( a , b )
        self.push_queue.put((MSG_EVALUATE, string))
        # 3. Send notification to other peers
        self.push_queue.put((MSG_HIGHLIGHT, lines[0], lines[1]))
        return "break"

class ThreadSafeText(Text):
    def __init__(self, root, **options):
        Text.__init__(self, root.root, **options)
        self.queue = Queue.Queue()
        #help(self.dlineinfo)
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

                            elif line > 1 and col == 0:

                                index = "{}.end".format(line-1,)

                                self.delete(index)

                            this_peer.move(line, col)

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
                        #line = int(msg['row'])
                        #col  = int(msg['col'])

                        #index = "{}.{}".format(line, col)

                        if len(char) > 0 and this_peer.hasSelection():

                            this_peer.deleteSelection()

                        # self.insert(index, char)
                        self.insert(this_peer.mark, char)

                        line, col = (int(i) for i in self.index(this_peer.mark).split('.'))

                        this_peer.move(line, col)

                    elif msg['type'] == MSG_GET_ALL:

                        # Return the contents of the text box

                        text = self.get("1.0", END)

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

PeerColours = {"red"    : "white",
               "green"  : "white",
               "blue"   : "white",
               "yellow" : "black",
               "purple" : "white" }

class Peer:
    """ Class representing the connected performers within the Tk Widget
    """
    def __init__(self, id_num, widget):
        self.id = id_num
        self.root = widget

        self.name = StringVar()
        
        self.bg = sorted(PeerColours.keys())[self.id]
        self.fg = PeerColours[self.bg]
        
        self.label = Label(self.root,
                           textvariable=self.name,
                           bg=self.bg,
                           fg=self.fg,
                           font="Font")

        self.insert = Label(self.root,
                            bg=self.bg,
                            fg=self.fg,
                            text="" )

        self.tag_name = "tag_" + str(self.id)
        self.mark     = "mark_" + str(self.id)
        self.root.mark_set(self.mark, "0.0")

        # Tracks a peer's selection amount
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        self.root.tag_config(self.tag_name, background=self.bg)

        self.char_w = self.root.font.measure(" ")
        self.char_h = self.root.font.metrics("linespace")

        self.name.set("Unnamed Peer")
        self.move(1,0)

    def __str__(self):
        return str(self.name.get())
        
    def move(self, row, col):
        """ Updates information about this Peer from a network message.
            TODO - Add an insert cursor for each peer """

        x = (self.char_w * (col + 1)) % self.root.winfo_width()
        y = self.root.dlineinfo("{}.{}".format(row, col))

        # Only move the cursor if we have a valid index
        if y is not None:
            
            self.label.place(x=x, y=y[1]+self.char_h)
        return

    def select(self, start, end):
        """ Highlights text selected by this peer"""
        if start != end != "0.0":
            self.sel_start = start
            self.sel_end   = end
            self.root.tag_add(self.tag_name, self.sel_start, self.sel_end)
        else:
            self.root.tag_remove(self.tag_name, self.sel_start, self.sel_end)
            self.sel_start = start
            self.sel_end   = end            
        return

    def remove(self):
        self.label.destroy()
        return
    
    def hasSelection(self):
        return self.sel_start != self.sel_end != "0.0"
    
    def deleteSelection(self):
        self.root.tag_remove(self.tag_name, self.sel_start, self.sel_end)
        self.root.delete(self.sel_start, self.sel_end)
        self.sel_start = "0.0"
        self.sel_end   = "0.0"
        return

    def highlightBlock(self, lines):

        a, b = (int(x) for x in lines)

        if a == b: b += 1

        for line in range(a, b):
            start = "%d.0" % line
            end   = "%d.end" % line

            # Highlight text only to last character, not whole line

            self.highlight(start, end)
            
        # Unhighlight the line of text

        self.root.master.after(200, self.unhighlight)

        return

    def highlight(self, start, end):
        self.root.tag_add("code", start, end)
        self.root.tag_config("code", background=self.bg, foreground=self.fg)
        
        return

    def unhighlight(self):
        self.root.tag_delete("code")
        return
    
    def __eq__(self, other):
        return self.id == other
    def __ne__(self, other):
        return self.id != other
        

if __name__ == "__main__":
    # Testing
    i = Interface()
    i.run()
