from ..config import *
from ..message import *
from ..logfile import Log

from textbox import ThreadSafeText
from console import Console
from peer import Peer
from drag import Dragbar
from bracket import BracketHandler
from line_numbers import LineNumbers
from menu_bar import MenuBar

from Tkinter import *
import tkFileDialog
import os.path
import tkFont
import Queue
import sys
import webbrowser

class Interface:
    def __init__(self, title, language):

        self.lang = language()
        
        self.root=Tk()
        self.root.configure(background="black")
        self.root.title(title)

        self.root.columnconfigure(0, weight=0) # Line numbers
        self.root.columnconfigure(1, weight=1) # Text and console

        self.root.rowconfigure(0, weight=1) # Textbox
        self.root.rowconfigure(1, weight=0) # Dragbar
        self.root.rowconfigure(2, weight=0) # Console
        
        self.root.protocol("WM_DELETE_WINDOW", self.kill )

        icon = os.path.join(os.path.dirname(__file__), "img", "icon")

        try:

            # Use .ico file by default
            self.root.iconbitmap(icon + ".ico")
            
        except:

            # Use .gif if necessary
            self.root.tk.call('wm', 'iconphoto', self.root._w, PhotoImage(file=icon + ".gif"))

        # Menubar
        self.menu = MenuBar(self, visible = True)

        # Log-file import
        self.logfile = None

        # Scroll bar
        self.scroll = Scrollbar(self.root)
        self.scroll.grid(row=0, column=3, sticky='nsew')

        # Text box
        self.text=ThreadSafeText(self, bg="black", fg="white", insertbackground="black", height=15, bd=0)
        self.text.grid(row=0, column=1, sticky="nsew", columnspan=2)
        self.scroll.config(command=self.text.yview)

        # Line numbers
        self.line_numbers = LineNumbers(self.text, width=30, bg="black", bd=0, highlightthickness=0)
        self.line_numbers.grid(row=0, column=0, sticky='nsew')
        
        # Drag is a small line that changes the size of the console
        self.drag = Dragbar( self )
        self.drag.grid(row=1, column=0, stick="nsew", columnspan=4)

        # Console Box
        self.console = Console(self.root, bg="black", fg="white", height=5, width=10, font="Font")
        self.console.grid(row=2, column=0, columnspan=2, stick="nsew")
        sys.stdout = self.console # routes stdout to print to console

        # Statistics Graphs
        self.graphs = Canvas(self.root, bg="black", width=250, bd=0, relief="sunken")
        self.graphs.grid(row=2, column=2, sticky="nsew")
        self.graph_queue = Queue.Queue()

        # Console scroll bar
        self.c_scroll = Scrollbar(self.root)
        self.c_scroll.grid(row=2, column=3, sticky='nsew')
        self.c_scroll.config(command=self.console.yview)

        # Key bindings
        
        CtrlKey = "Command" if SYSTEM == MAC_OS else "Control"

        self.text.bind("<Key>",             self.KeyPress)
        self.text.bind("<{}-Return>".format(CtrlKey), self.Evaluate)
        self.text.bind("<{}-Right>".format(CtrlKey), self.CtrlRight)
        self.text.bind("<{}-Left>".format(CtrlKey), self.CtrlLeft)
        self.text.bind("<{}-Home>".format(CtrlKey), self.CtrlHome)
        self.text.bind("<{}-End>".format(CtrlKey), self.CtrlEnd)
        self.text.bind("<{}-period>".format(CtrlKey), self.stopSound)

        self.text.bind("<{}-m>".format(CtrlKey), self.ToggleMenu)

        # Key bindings to handle select
        self.text.bind("<Shift-Left>",  self.SelectLeft)
        self.text.bind("<Shift-Right>", self.SelectRight)
        self.text.bind("<Shift-Up>",    self.SelectUp)
        self.text.bind("<Shift-Down>",  self.SelectDown)
        self.text.bind("<Shift-End>",   self.SelectEnd)
        self.text.bind("<Shift-Home>",  self.SelectHome)
        self.text.bind("<{}-a>".format(CtrlKey), self.SelectAll)

        # Copy and paste key bindings

        self.text.bind("<{}-c>".format(CtrlKey), self.Copy)
        self.text.bind("<{}-x>".format(CtrlKey), self.Cut)
        self.text.bind("<{}-v>".format(CtrlKey), self.Paste)

        # Undo -- not implemented
        self.text.bind("<{}-z>".format(CtrlKey), self.Undo)        

        # Handling mouse events
        self.leftMouse_isDown = False
        self.leftMouseClickIndex = "0.0"
        self.text.bind("<Button-1>", self.leftMousePress)
        self.text.bind("<B1-Motion>", self.leftMouseDrag)
        self.text.bind("<ButtonRelease-1>", self.leftMouseRelease)
        
        self.text.bind("<Button-2>", self.rightMousePress) # disabled

        # Local execution (only on the local machine)

        self.text.bind("<Alt-Return>", self.LocalEvaluate)

        # Disabled Key bindings (for now)

        for key in "qwertyuiopsdfghjklbnm/":

            self.text.bind("<{}-{}>".format(CtrlKey, key), lambda e: "break")

        # Allowed key-bindings

        self.text.bind("<{}-equal>".format(CtrlKey),  self.IncreaseFontSize)
        self.text.bind("<{}-minus>".format(CtrlKey),  self.DecreaseFontSize)

        self.ignored_keys = (CtrlKey + "_L", CtrlKey + "_R", "sterling")

        # Directional commands

        self.directions = ("Left", "Right", "Up", "Down", "Home", "End")

        # Information about brackets

        self.handle_bracket = BracketHandler(self)

        self.closing_bracket_types = [")", "]", "}"]

        # Store information about the last key pressed
        self.last_keypress  = ""
        self.last_row       = 0
        self.last_col       = 0

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
        try:
            self.root.mainloop()
        except (KeyboardInterrupt, SystemExit):
            self.kill()
        return
        
    def kill(self):
        try:
            self.pull.kill()
            self.push.kill()
            self.text.lang.kill()
            if self.logfile:
                self.logfile.stop()
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

    def stopSound(self, event):
        """ Sends a kill all sound message to the server based on the language """
        self.push_queue.put( MSG_EVALUATE_STRING(-1, self.lang.stop_sound(), reply=1) )
        return "break"

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

        max_height = self.graphs.winfo_height()

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
        self.root.after(30, self.update_send)
        return
    
    def KeyPress(self, event):
        """ 'Pushes' the key-press to the server.
        """

        # TODO -> Creative Constraints
        # if not constraint_satisfied(event, self.text): return

        # Ignore the CtrlKey and non-ascii chars

        if event.keysym in self.ignored_keys: return "break"
        
        # row, col = self.text.index(INSERT).split(".")
        row, col = self.text.index(self.text.marker.mark).split(".")
        row = int(row)
        col = int(col)

        # Un-highlight any brackets

        self.text.tag_remove("tag_open_brackets", "1.0", END)

        """
        if self.text.alone(self.text.marker):

            reply = 0

        else:

            reply = 1
        """

        reply = 1 # Force all messages to go via the server

        # Set to None if not inserting text

        ret = "break"

        if event.keysym == "Delete":
            
            self.push_queue.put( MSG_DELETE(-1, row, col, reply) )

        elif event.keysym == "BackSpace":

            # Only add a backspace if the last has been updated

            if (self.last_keypress, self.last_row, self.last_col) != ("BackSpace", row, col):
            
                self.push_queue.put( MSG_BACKSPACE(-1, row, col, reply) )

        # Handle key board movement

        elif event.keysym in self.directions:

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

            # Add to queue -- and unselect any characters
            
            self.push_queue.put( MSG_SET_MARK(-1, row, col, reply) )

            # if there is some selected text, de-select

            if self.text.marker.hasSelection():

                self.push_queue.put( MSG_SELECT(-1, "0.0", "0.0") )

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

            if char in self.closing_bracket_types:

                # Work out if we need to add this bracket

                text = self.text.readlines()

                # "insert" the bracket in the text to simulate actually adding it

                try:

                    text[row] = text[row][:col] + char + text[row][col:]

                except IndexError as e:

                    stdout("IndexError", e)
                    stdout(row, col, text)                    

                # If we need to add a closing bracket, just insert

                if self.handle_bracket.is_inserting_bracket(text, row, col, event.char):

                    self.push_queue.put( MSG_INSERT(-1, char, row, col, reply) )

                # else, move to the right one space

                else:

                    new_row, new_col = self.Right(row, col)

                    self.push_queue.put( MSG_SET_MARK(-1, new_row, new_col, reply) )

                # Work out where the appropriate enclosing bracket is and send a message to highlight

                loc = self.handle_bracket.find_starting_bracket(text, row, col - 1, event.char)

                if loc is not None:

                    row1, col1 = loc
                    row2, col2 = row, col

                    self.push_queue.put( MSG_BRACKET(-1, row1, col1, row2, col2, reply))

            # Add any other character

            else:

                self.push_queue.put( MSG_INSERT(-1, char, row, col, reply) )

        # Update markers
        # self.text.refreshPeerLabels()

        # Remove selections
        # self.text.tag_remove(SEL, "1.0", END)

        # Store the key info

        self.last_keypress  = event.keysym
        self.last_row       = row
        self.last_col       = col
        
        # Make sure the user sees their cursor

        self.text.see(self.text.marker.mark)
    
        return ret

    """ Handling changes in selected areas """

    def UpdateSelect(self, last_row, last_col, new_row, new_col):
        try:
            start = self.text.index(self.text.marker.sel_tag + ".first")
            end   = self.text.index(self.text.marker.sel_tag + ".last")
            # Whchever (start or end) is equal to last_row/col combo, we update
            old_index = "{}.{}".format(last_row, last_col)
            new_index = "{}.{}".format(new_row, new_col)
            if start == old_index:
                start = new_index
            elif end == "{}.{}".format(last_row, last_col):
                end   = new_index
        except TclError as e:
            start = "{}.{}".format(last_row, last_col)
            end   = "{}.{}".format(new_row, new_col)

        self.push_queue.put( MSG_SELECT(-1, start, end) )
        self.push_queue.put( MSG_SET_MARK(-1, new_row, new_col, 1) )
            
        return "break"

    def SelectLeft(self, event):
        # self.text.marker.mark # use this instead of INSERT
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = self.Left(row1, col1)
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"

    def SelectRight(self, event):
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = self.Right(row1, col1)
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"
    
    def SelectUp(self, event):
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = self.Up(row1, col1)
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"
    
    def SelectDown(self, event):
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = self.Down(row1, col1)
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"

    def SelectEnd(self, event):
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = (int(i) for i in self.text.index("{}.end".format(row1)).split("."))
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"

    def SelectHome(self, event):
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = (int(i) for i in self.text.index("{}.0".format(row1)).split("."))
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"

    def SelectAll(self, event=None):
        start = "1.0"
        end   = self.text.index(END)
        self.push_queue.put( MSG_SELECT(-1, start, end) )
        self.push_queue.put( MSG_SET_MARK(-1, 1, 0, 1) )
        return "break"

    def Selection(self, event=None):
        """ Handles selected areas """
        # stdout("hello")
        return "break"

    """ Update colour / formatting """

    def colour_line(self, line):
        """ Embold keywords defined in Interpreter.py """

        start, end = "{}.0".format(line), "{}.end".format(line)
        string = self.text.get(start, end)

        self.text.tag_remove("tag_bold", start, end)
        
        for match in self.lang.re.finditer(string):
            start = "{}.{}".format(line, match.start())
            end   = "{}.{}".format(line, match.end())
            self.text.tag_add("tag_bold", start, end)
            
        return

    """ Ctrl-Home and Ctrl-End Handling """

    def CtrlHome(self, event):
        # Add to queue
        self.push_queue.put( MSG_SET_MARK(-1, 1, 0) )

        # Update the actual insert mark
        self.setInsert( "1.0" )

        # Make sure the user sees their cursor
        self.text.see(self.text.marker.mark)
        
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
        index = self.text.index(self.text.marker.mark)

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
        index = self.text.index(self.text.marker.mark)

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
        return row, col
    
    def Right(self, row, col):
        end_col = int(self.text.index("{}.end".format(row)).split(".")[1])          
        if col == end_col:
            if "{}.{}".format(row + 1, 0) != self.text.index(END):
                col = 0
                row += 1
        else:
            col += 1        
        return row, col

    def Down(self, row, col):
        """ For up and down presses, find the index based on height """

        index = "{}.{}".format(row, col)

        try:

            x,y,w,h = self.text.bbox(index)

        except TypeError:

            y, h = self.text.winfo_height(), self.text.pady

        if y + h < self.text.winfo_height() - self.text.pady:

            next_index = self.text.index("@{},{}".format(x, y + h))

            row, col = [int(val) for val in next_index.split(".")]

        else:

            row += 1
            next_end_col = int(self.text.index("{}.end".format(row)).split(".")[1])
            col = min(col, next_end_col)
            
        return row, col
    
    def Up(self, row, col):
        """ For up and down presses, find the index based on height """

        #if row > 1:
        if True:

            index = "{}.{}".format(row, col)

            try:

                x,y,w,h = self.text.bbox(index)

            except TypeError:

                x, y, h = 0, 0, 1

            if y >= h:

                next_index = self.text.index("@{},{}".format(x, y - h))

                row, col = [int(val) for val in next_index.split(".")]

            elif row > 1:

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
        cur_x, cur_y = self.text.index(self.text.marker.mark).split(".")
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


    def LocalEvaluate(self, event=None):
        # 1. Get the block of code
        lines = self.currentBlock()
        # 2. Convert to string
        a, b = ("%d.0" % n for n in lines)
        string = self.text.get( a , b )
        # 3. Evaluate locally
        self.text.lang.evaluate(string, str(self.text.marker), self.text.marker.bg)
        # 4. Highlight the text
        self.text.peers[self.text.local_peer].highlightBlock((lines[0], lines[1]))
        return "break"

    def Evaluate(self, event=None):
        # 1. Get the block of code
        lines = self.currentBlock()
        # 2. Send as string to the server
        a, b = ("%d.0" % n for n in lines)
        string = self.text.get( a , b ).lstrip()
        if string != "":
            # 3. Send notification to other peers
            self.push_queue.put( MSG_EVALUATE_BLOCK(-1, lines[0], lines[1], reply=1) )
        return "break"

    def ChangeFontSize(self, amount):
        self.root.grid_propagate(False)
        for font in ("Font", "BoldFont"):
            font = tkFont.nametofont(font)
            size = max(8, font.actual()["size"] + amount)
            font.configure(size=size)
            self.text.char_w = self.text.font.measure(" ")
            self.text.char_h = self.text.font.metrics("linespace")
        return

    def DecreaseFontSize(self, event):
        self.ChangeFontSize(-1)
        self.line_numbers.config(width=self.line_numbers.winfo_width() - 2)
        self.text.refreshPeerLabels() # -- why this doesn't work?
        return 'break'

    def IncreaseFontSize(self, event=None):
        self.ChangeFontSize(+1)
        self.line_numbers.config(width=self.line_numbers.winfo_width() + 2)
        self.text.refreshPeerLabels()
        return 'break'

    def leftMouseRelease(self, event=None):
        self.leftMouse_isDown = False
        index = self.text.index("@{},{}".format(event.x, event.y))
        row, col = index.split(".")
        self.push_queue.put( MSG_SET_MARK(-1, int(row), int(col), 1) )
        return "break"

    def leftMouseDrag(self, event):
        if self.leftMouse_isDown:
            sel_start = self.leftMouseClickIndex
            sel_end   = self.text.index("@{},{}".format(event.x, event.y))

            start, end = self.text.sort_indices([sel_start, sel_end])

            self.push_queue.put( MSG_SELECT(-1, start, end) )
            
        return "break"

    def leftMousePress(self, event):
        ''' Override for left mouse click '''

        self.leftMouse_isDown = True

        # Get text index of click location

        self.leftMouseClickIndex = index = self.text.index("@{},{}".format( event.x, event.y ))

        row, col = index.split(".")

        # Set the mark

        self.push_queue.put( MSG_SET_MARK(-1, row, col) )

        self.push_queue.put( MSG_SELECT(-1, "0.0", "0.0") )

        # Make sure the text box gets focus

        self.text.focus_set()        

        return "break"

    def rightMousePress(self, event):
        return "break"

    def Undo(self, event):
        ''' Override for Ctrl+Z -- Not implemented '''
        # self.text.edit_undo()
        return "break"

    def Copy(self, event=None):
        ''' Override for Ctrl+C '''
        if self.text.marker.hasSelection():
            text = self.text.get(self.text.marker.sel_start, self.text.marker.sel_end)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        return "break"

    def Cut(self, event=None):
        if self.text.marker.hasSelection():
            text = self.text.get(self.text.marker.sel_start, self.text.marker.sel_end)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            row, col = self.convert(self.text.index(self.text.marker.mark))
            self.push_queue.put( MSG_BACKSPACE(-1, row, col) )
        return "break"
    
    def Paste(self, event=None):
        text = self.root.clipboard_get()
        row, col = self.convert(self.text.index(self.text.marker.mark))
        self.push_queue.put( MSG_INSERT(-1, text, row, col) )
        return "break"

    def ToggleMenu(self, event=None):
        self.menu.toggle()
        return "break"

    def OpenGitHub(self, event=None):
        webbrowser.open("https://github.com/Qirky/Troop")

    def ImportLog(self):
        """ Imports a logfile generated by run-server.py --log and 'recreates' the performance """
        logname = tkFileDialog.askopenfilename()        
        self.logfile = Log(logname)
        self.logfile.set_marker(self.text.marker)
        self.logfile.recreate()
        return
