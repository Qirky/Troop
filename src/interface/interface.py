from ..config import *
from ..message import *

from textbox import ThreadSafeText
from console import Console
from peer import Peer

from Tkinter import *
import tkFont
import Queue

# TODO
"""
- Handle mouse click
"""

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
        self.text=ThreadSafeText(self, bg="black", fg="white", insertbackground="white", height=15)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.scroll.config(command=self.text.yview)

        # Remove standard highlight tag config
        self.text.tag_config(SEL, background="black")

        # Console Box
        self.console = Console(self.root, bg="black", fg="white", height=6, font="Font")
        self.console.grid(row=1, column=0, stick="nsew")
        self.c_scroll = Scrollbar(self.root)
        self.c_scroll.grid(row=1, column=1, sticky='nsew')
        self.c_scroll.config(command=self.console.yview)

        # Key bindings
        
        CtrlKey = "Command" if SYSTEM == MAC_OS else "Control"

        self.text.bind("<Key>",             self.KeyPress)

        self.text.bind("<<Selection>>",     self.Selection)

        self.text.bind("<{}-Return>".format(CtrlKey),  self.Evaluate)

        self.text.bind("<{}-Home>".format(CtrlKey),  self.CtrlHome)

        self.text.bind("<{}-End>".format(CtrlKey),   self.CtrlEnd)

        # Key bindings to handle select
        self.text.bind("<Shift-Left>",  self.SelectLeft)
        self.text.bind("<Shift-Right>", self.SelectRight)
        self.text.bind("<Shift-Up>",    self.SelectUp)
        self.text.bind("<Shift-Down>",  self.SelectDown)
        self.text.bind("<Shift-End>",   self.SelectEnd)
        self.text.bind("<Shift-Home>",  self.SelectHome)

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
        self.text.focus_force()

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

        elif event.keysym == "BackSpace":
            self.push_queue.put((MSG_BACKSPACE, row, col))

        # Handle key board movement

        elif event.keysym in self.directions:

            if event.keysym == "Left":
                row, col = self.Left(row, col)

            elif event.keysym == "Right":
                row, col = self.Right(row, col)

            elif event.keysym == "Up":
                row, col = self.Up(row, col)

            elif event.keysym == "Down":
                row, col = self.Down(row, col)

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

        # Remove selections

        self.text.tag_remove(SEL, "1.0", END)
        self.Selection()
    
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
            self.push_queue.put((MSG_SELECT, self.sel_start, self.sel_end))
        return

    """ Ctrl-Home and Ctrl-End Handling """

    def CtrlHome(self, event):
        # Add to queue
        self.push_queue.put((MSG_SET_MARK, 1, 0))

        # Update the actual insert mark
        self.text.mark_set(INSERT, "1.0")
        
        return "break"

    def CtrlEnd(self, event):
        row, col = self.text.index(END).split(".")

        # Add to queue
        self.push_queue.put((MSG_SET_MARK, row, col))

        # Update the actual insert mark
        self.text.mark_set(INSERT, END)
        
        return "break"

    """ Directional key-presses """    

    def Left(self, row, col):
        if col > 0:
            col -= 1
        elif row > 1:
            prev_line = self.text.index("{}.end".format(row-1)).split(".")
            row = int(prev_line[0])
            col = int(prev_line[1])
        return row, col
    
    def Right(self, row, col):
        end_col = int(self.text.index("{}.end".format(row)).split(".")[1])          
        if col == end_col:
            col = 0
            row += 1
        else:
            col += 1
        return row, col
    
    def Down(self, row, col):
        row += 1
        next_end_col = int(self.text.index("{}.end".format(row)).split(".")[1])
        col = min(col, next_end_col)
        return row, col
    
    def Up(self, row, col):
        if row > 1:
            row -= 1
            prev_end_col = int(self.text.index("{}.end".format(row)).split(".")[1])
            col = min(col, prev_end_col)
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
