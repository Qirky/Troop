from ..config import *
from ..message import *

from textbox import ThreadSafeText
from console import Console
from peer import Peer

from Tkinter import *
import tkFont
import Queue
import sys

class Interface:
    def __init__(self, title="Troop"):
        
        self.root=Tk()
        self.root.title(title)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=2)
        self.root.protocol("WM_DELETE_WINDOW", self.kill )

        # Scroll bar
        self.scroll = Scrollbar(self.root)
        self.scroll.grid(row=0, column=2, sticky='nsew')

        # Text box
        self.text=ThreadSafeText(self, bg="black", fg="white", insertbackground="black", height=15)
        self.text.grid(row=0, column=0, sticky="nsew", columnspan=2)
        self.scroll.config(command=self.text.yview)

        # Remove standard highlight tag config
        self.text.tag_config(SEL, background="black")

        # Console Box
        self.console = Console(self.root, bg="black", fg="white", height=5, width=10, font="Font")
        self.console.grid(row=1, column=0, stick="nsew")
        self.c_scroll = Scrollbar(self.root)
        self.c_scroll.grid(row=1, column=2, sticky='nsew')
        self.c_scroll.config(command=self.console.yview)
        sys.stdout = self.console

        # Statistics Graphs
        self.graphs = Canvas(self.root, bg="black", width=250)
        self.graphs.grid(row=1, column=1, sticky="nsew")
        self.graph_queue = Queue.Queue()

        # Key bindings
        
        CtrlKey = "Command" if SYSTEM == MAC_OS else "Control"

        self.text.bind("<Key>",             self.KeyPress)
        self.text.bind("<<Selection>>",     self.Selection)
        self.text.bind("<{}-Return>".format(CtrlKey), self.Evaluate)
        self.text.bind("<{}-Right>".format(CtrlKey), self.CtrlRight)
        self.text.bind("<{}-Left>".format(CtrlKey), self.CtrlLeft)
        self.text.bind("<{}-Home>".format(CtrlKey), self.CtrlHome)
        self.text.bind("<{}-End>".format(CtrlKey), self.CtrlEnd)

        # Key bindings to handle select
        self.text.bind("<Shift-Left>",  self.SelectLeft)
        self.text.bind("<Shift-Right>", self.SelectRight)
        self.text.bind("<Shift-Up>",    self.SelectUp)
        self.text.bind("<Shift-Down>",  self.SelectDown)
        self.text.bind("<Shift-End>",   self.SelectEnd)
        self.text.bind("<Shift-Home>",  self.SelectHome)

        # Copy and paste key bindings

        self.text.bind("<{}-c>".format(CtrlKey), self.Copy)
        self.text.bind("<{}-x>".format(CtrlKey), self.Cut)
        self.text.bind("<{}-v>".format(CtrlKey), self.Paste)

        # Undo -- not implemented
        self.text.bind("<{}-z>".format(CtrlKey), self.Undo)        

        # Handling mouse events
        self.text.bind("<Button-1>", self.leftMousePress)
        self.text.bind("<Button-2>", self.rightMousePress)

        # Local execution (only on the local machine)

        self.text.bind("<Alt-Return>", self.LocalEvaluate)

        # Disabled Key bindings (for now)

        for key in "qwertyuiopasdfghjklbnm":

            self.text.bind("<{}-{}>".format(CtrlKey, key), lambda e: "break")

        # Allowed key-bindings

        self.text.bind("<{}-equal>".format(CtrlKey),  self.IncreaseFontSize)
        self.text.bind("<{}-minus>".format(CtrlKey),  self.DecreaseFontSize)

        self.CtrlKeys = (CtrlKey + "_L", CtrlKey + "_R")

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
        self.text.focus_force()

        # Continually check for messages to be sent
        self.update_send()
        self.update_graphs()
        
    def run(self):
        self.root.mainloop()
        
    def kill(self):
        try:
            self.pull.kill()
            self.push.kill()
            self.text.lang.kill()
        except(Exception) as e:
            stdout(e)
        stdout("Quitting")
        self.root.destroy()

    @staticmethod
    def convert(index):
        return tuple(int(value) for value in str(index).split("."))

    def setMarker(self, id_num, name):
        self.text.local_peer = id_num
        self.text.marker=Peer(id_num, self.text)
        self.text.marker.name.set(name)
        self.text.marker.move(1,0)
        self.text.peers[id_num] = self.text.marker

        # Tell any other peers about this location
        self.push_queue.put( MSG_SET_MARK(-1, 1, 0, 0) )
        
        
        return

    def setInsert(self, index):
        ''' sets the INSERT and peer mark '''
        self.text.mark_set(INSERT, index)
        self.text.mark_set(self.text.marker.mark, index)
        return
        
    def write(self, msg):
        """ Writes a network message to the queue
        """
        # msg must be a Troop message
        assert isinstance(msg, MESSAGE)
        
        # Keep information about new peers

        if 'src_id' in msg:

            sender_id = msg['src_id']

            if sender_id not in self.text.peers:

                # Get peer's current location & name

                row  = self.pull(sender_id, "row")
                col  = self.pull(sender_id, "col")
                name = self.pull(sender_id, "name")

                self.text.peers[sender_id] = Peer(sender_id, self.text, row, col)
                self.text.peers[sender_id].name.set(name)

        # Add message to queue
        self.text.queue.put(msg)

        return

    def update_graphs(self):
        """ Continually counts the number of coloured chars
            and update self.graphs """
        # For each connected peer, find the range covered by the tag
        
        for peer in self.text.peers.values():

            tag_name = peer.text_tag

            loc = self.text.tag_ranges(tag_name)

            count = 0

            if len(loc) > 0:

                for i in range(0, len(loc), 2):

                    start, end = loc[i], loc[i+1]

                    start = self.convert(start)
                    end   = self.convert(end)

                    # If the range is on the same line, just count

                    if start[0] == end[0]:

                        count += (end[1] - start[1])

                    else:

                        # Get the first line

                        count += (self.convert(self.text.index("{}.end".format(start[0])))[1] - start[1])

                        # If it spans multiple lines, just count all characters

                        for line in range(start[0] + 1, end[0]):

                            count += self.convert(self.text.index("{}.end".format(line)))[1]

                        # Add the number of the last line

                        count += end[1]

            peer.count = count

        # Once we count all, work out percentages and draw graphs

        total = float(sum([p.count for p in self.text.peers.values()]))

        max_height = 250

        offset_x = 10
        offset_y = 10

        graph_w = 25

        for n, peer in enumerate(self.text.peers.values()):

            height = ((peer.count / total) * max_height) if total > 0 else 0

            x1 = (n * graph_w) + offset_x
            y1 = max_height + offset_y
            x2 = x1 + graph_w
            y2 = y1 - (int(height))
            self.graphs.coords(peer.graph, (x1, y1, x2, y2))

            # Write number / name?
                    
        self.root.update_idletasks()
        self.root.after(100, self.update_graphs)
        return

    def update_send(self):
        """ Sends any keypress information to the server
        """
        try:
            while True:
                self.push( self.push_queue.get_nowait() )
                self.root.update_idletasks()
        # Break when the queue is empty
        except Queue.Empty:
            pass

        # Recursive call
        self.root.after(50, self.update_send)
        return
    
    def KeyPress(self, event):
        """ 'Pushes' the key-press to the server.
        """

        # TODO -> Creative Constraints
        # if not constraint_satisfied(event, self.text): return

        # Ignore the CtrlKey

        if event.keysym in self.CtrlKeys: return
        
        row, col = self.text.index(INSERT).split(".")
        row = int(row)
        col = int(col)

        # Reply is set to True by default. If there are no other peers
        # on the same line, set to 0 and perform keypress action locally

        if self.text.alone(self.text.marker):

            reply = 0

        else:

            reply = 1

        # Set to None if not inserting text

        ret = "break"

        if event.keysym == "Delete":

            # Deletes are tricky - send to server to make sure they work

            reply = 1

            self.push_queue.put( MSG_DELETE(-1, row, col, reply) )

        elif event.keysym == "BackSpace":

            reply = 0
            
            self.push_queue.put( MSG_BACKSPACE(-1, row, col, reply) )
            
            if not reply:

                self.text.handle_backspace(self.text.marker, row, col)

        # Handle key board movement

        elif event.keysym in self.directions:

            # reply = 1

            old_row, old_col = row, col

            if event.keysym == "Left":
                row, col = self.Left(old_row, old_col)

            elif event.keysym == "Right":
                row, col = self.Right(old_row, old_col)

            elif event.keysym == "Up":
                row, col = self.Up(old_row, old_col)

            elif event.keysym == "Down":
                row, col = self.Down(old_row, old_col)

            elif event.keysym == "Home":
                col = 0

            elif event.keysym == "End":
                col = int(self.text.index("{}.end".format(row)).split(".")[1])

            # Move the label locally if not getting a reply from server

            if not reply:

                # Update the INSERT marker

                self.setInsert( "{}.{}".format(row, col) )

                self.text.marker.move(row, col)

            # Add to queue
            self.push_queue.put( MSG_SET_MARK(-1, row, col, reply) )                       

        # Inserting a character

        else:

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

            self.push_queue.put( MSG_INSERT(-1, char, row, col, reply) )

            if not reply:

                self.text.handle_insert(self.text.marker, char, row, col)

        # Update markers
        self.text.refreshPeerLabels()

        # Remove selections

        self.text.tag_remove(SEL, "1.0", END)
        self.Selection()

        # Make sure the user sees their cursor

        self.text.see(INSERT)
    
        return ret

    """ Handling changes in selected areas """

    def SelectLeft(self, event):      
        return

    def SelectRight(self, event):
        return
    
    def SelectUp(self, event):
        return
    
    def SelectDown(self, event):
        return

    def SelectEnd(self, event):
        return

    def SelectHome(self, event):
        return

    def Selection(self, event=None):
        """ Handles selected areas """
        try:
            self.sel_start = self.text.index(SEL_FIRST)
            self.sel_end   = self.text.index(SEL_LAST)
        except:
            self.sel_start = self.text.index(INSERT)
            self.sel_end   = self.text.index(INSERT)
        if event is not None:       
            self.push_queue.put( MSG_SELECT(-1, self.sel_start, self.sel_end) )
        return

    """ Ctrl-Home and Ctrl-End Handling """

    def CtrlHome(self, event):
        # Add to queue
        self.push_queue.put( MSG_SET_MARK(-1, 1, 0) )

        # Update the actual insert mark
        self.setInsert( "1.0" )

        # Make sure the user sees their cursor
        self.text.see(INSERT)
        
        return "break"

    def CtrlEnd(self, event):
        row, col = self.text.index(END).split(".")

        # Add to queue
        self.push_queue.put( MSG_SET_MARK(-1, row, col) )

        # Update the actual insert mark
        self.setInsert( END )
        
        return "break"

    def findWordLeft(self):
        # Go back until you find the next " "
        index = self.text.index(INSERT)

        if index == "1.0":

            return 1, 0

        row, col = self.convert(index)

        while col == 0:

            row, col = self.convert(self.text.index("{}.end".format(row-1)))

        while self.text.get("{}.{}".format(row, col-1)) == " " and col > 0:

            col -= 1

        for col in range(col, 0, -1):

            index="{}.{}".format(row, col - 1)

            if self.text.get(index) == " ":

                return row, col

        return row, 0


    def CtrlLeft(self, event):

        row, col = self.findWordLeft()

        self.setInsert( "{}.{}".format(row,col) )

        self.push_queue.put( MSG_SET_MARK(-1, row, col) )
                    
        return "break"

    def CtrlRight(self, event):

        row, col = self.findWordRight()

        self.setInsert( "{}.{}".format(row,col) )

        self.push_queue.put( MSG_SET_MARK(-1, row, col) )
                    
        return "break"
        

    def findWordRight(self):
        index = self.text.index(INSERT)

        row, col = self.convert(index)

        _, end_col = self.convert(self.text.index("{}.end".format(row)))

        while self.text.get("{}.{}".format(row, col)) == " " and col < end_col:

            col += 1

        end_row, end_col = self.convert(self.text.index(END))

        for r in range(row, end_row + 1):
            
            if r == row:
                start_col = col

            else:
                
                start_col = 0

            _, end_c = self.convert(self.text.index("{}.end".format(row)))

            for c in range(start_col, end_c):

                index="{}.{}".format(r, c)

                if self.text.get(index) == " ":

                    return r, c
                    
        return end_row, end_col

    """ Directional key-presses """    

    def Left(self, row, col):
        if col > 0:
            col -= 1
        elif row > 1:
            prev_line = self.text.index("{}.end".format(row-1)).split(".")
            row = int(prev_line[0])
            col = int(prev_line[1])

        # Make sure the user sees their cursor
        self.text.see(INSERT)
        
        return row, col
    
    def Right(self, row, col):
        end_col = int(self.text.index("{}.end".format(row)).split(".")[1])          
        if col == end_col:
            col = 0
            row += 1
        else:
            col += 1

        # Make sure the user sees their cursor
        self.text.see(INSERT)
        
        return row, col
    
    def Down(self, row, col):
        row += 1
        next_end_col = int(self.text.index("{}.end".format(row)).split(".")[1])
        col = min(col, next_end_col)

        # Make sure the user sees their cursor
        self.text.see(INSERT)
        
        return row, col
    
    def Up(self, row, col):
        if row > 1:
            row -= 1
            prev_end_col = int(self.text.index("{}.end".format(row)).split(".")[1])
            col = min(col, prev_end_col)

        # Make sure the user sees their cursor
        self.text.see(INSERT)
        
        return row, col

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


    def LocalEvaluate(self, event):
        # 1. Get the block of code
        lines = self.currentBlock()
        # 2. Convert to string
        a, b = ("%d.0" % n for n in lines)
        string = self.text.get( a , b )
        # 3. Evaluate locally
        self.text.lang.evaluate(string)
        # 4. Highlight the text
        self.text.peers[self.text.local_peer].highlightBlock((lines[0], lines[1]))
        return "break"

    def Evaluate(self, event):
        # 1. Get the block of code
        lines = self.currentBlock()
        # 2. Send as string to the server
        a, b = ("%d.0" % n for n in lines)
        string = self.text.get( a , b )
        self.push_queue.put( MSG_EVALUATE(-1, string) )
        # 3. Send notification to other peers
        self.push_queue.put( MSG_HIGHLIGHT(-1, lines[0], lines[1], 0) )
        # 4. Highlight the text
        self.text.peers[self.text.local_peer].highlightBlock((lines[0], lines[1]))
        return "break"

    def ChangeFontSize(self, amount):
        self.root.grid_propagate(False)
        font = tkFont.nametofont("Font")
        size = max(8, font.actual()["size"] + amount)
        font.configure(size=size)
        self.text.char_w = self.text.font.measure(" ")
        self.text.char_h = self.text.font.metrics("linespace")
        return

    def DecreaseFontSize(self, event):
        self.ChangeFontSize(-2)
        self.text.refreshPeerLabels()
        return 'break'

    def IncreaseFontSize(self, event):
        self.ChangeFontSize(+2)
        self.text.refreshPeerLabels()
        return 'break'

    def leftMousePress(self, event):
        ''' Override for left mouse click '''

        # Get text index of click location

        index = self.text.index("@{},{}".format( event.x, event.y ))

        row, col = index.split(".")

        # Set the mark

        self.push_queue.put( MSG_SET_MARK(-1, row, col) )

        self.setInsert( index )

        # De-select text

        self.sel_start = self.text.index(INSERT)

        self.sel_end   = self.text.index(INSERT)

        self.push_queue.put( MSG_SELECT(-1, self.sel_start, self.sel_end) )

        # Make sure the text box gets focus

        self.text.focus_set()        

        return "break"

    def rightMousePress(self, event):
        return "break"

    def Undo(self, event):
        ''' Override for Ctrl+Z -- Not implemented '''
        # self.text.edit_undo()
        return "break"

    def Copy(self, event):
        ''' Override for Ctrl+C '''
        text = self.text.get(self.sel_start, self.sel_end)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        return "break"

    def Cut(self, event):
        text = self.text.get(self.sel_start, self.sel_end)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        row, col = self.convert(self.text.index(INSERT))
        self.push_queue.put( MSG_BACKSPACE(-1, row, col) )
        return "break"
    
    def Paste(self, event):
        text = self.root.clipboard_get()
        row, col = self.convert(self.text.index(INSERT))
        self.push_queue.put( MSG_INSERT(-1, text, row, col) )
        return "break"
