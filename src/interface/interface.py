from __future__ import absolute_import, print_function

from ..config import *
from ..message import *
from ..logfile import Log
from ..interpreter import *

from .textbox import ThreadSafeText
from .console import Console
from .peer import Peer
from .drag import Dragbar
from .bracket import BracketHandler
from .line_numbers import LineNumbers
from .menu_bar import MenuBar

try:
    from Tkinter import *
    import tkFileDialog
    import tkFont
except ImportError:
    from tkinter import *
    from tkinter import filedialog as tkFileDialog
    from tkinter import font as tkFont

try:
    import queue
except ImportError:
    import Queue as queue

import os, os.path
import time
import sys
import webbrowser

class BasicInterface:
    """ Class for displaying basic text input data.
    """
    def __init__(self):
        self.root=Tk()
        self.root.configure(background=COLOURS["Background"])
        
        self.is_logging = False
        self.logfile = None
        self.wait_msg = None
        self.waiting  = None

        # Store information about the last key pressed
        self.last_keypress  = ""
        self.last_row       = 0
        self.last_col       = 0
        
    def run(self):
        """ Starts the Tkinter loop and exits cleanly if interrupted"""
        try:
            self.root.mainloop()
        except (KeyboardInterrupt, SystemExit):
            self.kill()
        return
    
    def kill(self):
        """ Terminates cleanly """
        stdout("Quitting")
        self.root.destroy()
        return

    def reset_title(self):
        """ Overloaded in Interface class """
        return

    def colour_line(self, line):
        """ Embold keywords defined in `Interpreter.py` """

        # Get contents of the line

        start, end = "{}.0".format(line), "{}.end".format(line)
        
        string = self.text.get(start, end)

        # Go through the possible tags

        for tag_name, re_tag in self.lang.re.items():

            self.text.tag_remove(tag_name, start, end)
            
            for match in re_tag.finditer(string):
                
                tag_start = "{}.{}".format(line, match.start())
                tag_end   = "{}.{}".format(line, match.end())

                self.text.tag_add(tag_name, tag_start, tag_end)
                
        return

class DummyInterface(BasicInterface):
    """ Only implemented in server debug mode """
    def __init__(self):
        BasicInterface.__init__(self)
        self.lang = DummyInterpreter()
        self.text=ThreadSafeText(self, bg=COLOURS["Background"], fg="white", insertbackground=COLOURS["Background"], height=15, bd=0)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.text.marker = Peer(-1, self.text)

class Interface(BasicInterface):
    def __init__(self, title, language, logging=False):

        # Inherit

        BasicInterface.__init__(self)

        # Set language -- TODO have knowledge of language and set boolean to True

        self.lang = language()
        self.interpreters = {name: BooleanVar() for name in langnames}

        # Set logging

        if logging:

            self.set_up_logging()

        # Set title and configure the interface grid

        self.title = title
        
        self.root.title(self.title)

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

            try:
                # Use .gif if necessary
                self.root.tk.call('wm', 'iconphoto', self.root._w, PhotoImage(file=icon + ".gif"))

            except:

                # If there is no image, just ignore for now -- this is not good practice
                pass

        # Track whether user wants transparent background

        self.transparent = BooleanVar()
        self.transparent.set(False)

        # Scroll bar
        self.scroll = Scrollbar(self.root)
        self.scroll.grid(row=0, column=3, sticky='nsew')

        # Text box
        self.text=ThreadSafeText(self, bg=COLOURS["Background"], fg="white", insertbackground=COLOURS["Background"], height=15, bd=0)
        self.text.grid(row=0, column=1, sticky="nsew", columnspan=2)
        self.scroll.config(command=self.text.yview)

        # Line numbers
        self.line_numbers = LineNumbers(self.text, width=55, bg=COLOURS["Background"], bd=0, highlightthickness=0)
        self.line_numbers.grid(row=0, column=0, sticky='nsew')
        
        # Drag is a small line that changes the size of the console
        self.drag = Dragbar( self )
        self.drag.grid(row=1, column=0, stick="nsew", columnspan=4)

        # Console Box
        self.console = Console(self.root, bg=COLOURS["Console"], fg="white", height=5, width=10, font="Font")
        self.console.grid(row=2, column=0, columnspan=2, stick="nsew")
        sys.stdout = self.console # routes stdout to print to console

        # Statistics Graphs
        self.graphs = Canvas(self.root, bg=COLOURS["Stats"], width=450, bd=0, highlightthickness=0)
        self.graphs.grid(row=2, column=2, sticky="nsew")
        self.graph_queue = queue.Queue()

        # Console scroll bar
        self.c_scroll = Scrollbar(self.root)
        self.c_scroll.grid(row=2, column=3, sticky='nsew')
        self.c_scroll.config(command=self.console.yview)

        # Creative constraints

        from . import constraints
        constraints = vars(constraints)

        self.default_constraint  = "anarchy"
        self.creative_constraints = {name: BooleanVar() for name in constraints if not name.startswith("_")}
        self.creative_constraints[self.default_constraint].set(True)
        self.__constraint__ = constraints[self.default_constraint]()

        # Menubar

        self.menu = MenuBar(self, visible = True)

        # Key bindings
        
        CtrlKey = "Command" if SYSTEM == MAC_OS else "Control"

        self.text.bind("<Key>", self.KeyPress)
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
        
        # select_background
        self.text.tag_configure(SEL, background=COLOURS["Background"])   # Temporary fix - set normal highlighting to background colour
        self.text.bind("<<Selection>>", self.Selection)

        # Single line execution

        self.text.bind("<Alt-Return>", self.SingleLineEvaluate)

        # Disabled Key bindings (for now)

        disable = lambda e: "break"

        for key in list("qwertyuipdfghjklbm") + ["slash"]:

            self.text.bind("<{}-{}>".format(CtrlKey, key), disable)

        # Allowed key-bindings

        self.text.bind("<{}-equal>".format(CtrlKey),  self.IncreaseFontSize)
        self.text.bind("<{}-minus>".format(CtrlKey),  self.DecreaseFontSize)

        self.text.bind("<{}-s>".format(CtrlKey),  self.menu.save_file)
        self.text.bind("<{}-o>".format(CtrlKey),  self.menu.open_file)
        self.text.bind("<{}-n>".format(CtrlKey),  self.menu.new_file)

        self.ignored_keys = (CtrlKey + "_L", CtrlKey + "_R", "sterling")

        # Directional commands

        self.directions = ("Left", "Right", "Up", "Down", "Home", "End")

        # Information about brackets

        self.handle_bracket = BracketHandler(self)

        self.closing_bracket_types = [")", "]", "}"]

        # Selection indices
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        # Listener
        self.pull = lambda *x: None

        # Sender
        self.push = None
        self.push_queue = queue.Queue()

        # Set the window focus
        self.text.focus_force()

        # Continually check for messages to be sent
        self.update_send()
        self.update_graphs()
        
    def kill(self):
        """ Close socket connections and terminate the application """
        try:

            if len(self.text.peers) == 1:
                from time import sleep
                self.push(MSG_SET_ALL(self.text.marker.id, self.text.handle_getall(), -1))
                sleep(0.25)
                
            self.pull.kill()
            self.push.kill()
            self.lang.kill()
            if self.logfile:
                self.logfile.stop()
            if self.is_logging:
                self.log_file.close()
        except(Exception) as e:
            stdout(e)
        BasicInterface.kill(self)
        return

    @staticmethod
    def convert(index):
        """ Converts a Tkinter index into a tuple of integers """
        return tuple(int(value) for value in str(index).split("."))

    def createLocalMarker(self, id_num, name):
        """ Create the peer that is local to the client """
        self.text.local_peer = id_num
        self.text.marker=Peer(id_num, self.text)
        self.text.marker.name.set(name)
        self.text.marker.move(1,0)
        self.text.marker.graph  = self.graphs.create_rectangle(0,0,0,0, fill=self.text.marker.bg)
        self.text.peers[id_num] = self.text.marker

        # Tell any other peers about this location
        self.push_queue.put( MSG_SET_MARK(-1, 1, 0, 0) )
        
        return

    def stopSound(self, event):
        """ Sends a kill all sound message to the server based on the language """
        self.push_queue.put( MSG_EVALUATE_STRING(self.text.marker.id, self.lang.stop_sound() + "\n", reply=1) )
        return "break"

    def setInsert(self, index):
        ''' sets the INSERT and peer mark '''
        self.text.mark_set(INSERT, index)
        self.text.mark_set(self.text.marker.mark, index)
        return

    def reset_title(self):
        """ Resets any changes to the window's title """
        self.root.title(self.title)
        return

    def update_graphs(self):
        """ Continually counts the number of coloured chars and update self.graphs """

        # TODO -- draw graph for peers no longer connected?

        # Only draw graphs once the peer(s) connects

        if len(self.text.peers) == 0:

            self.root.after(100, self.update_graphs)

            return

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
        max_width  = self.graphs.winfo_width()

        # Gaps between edges

        offset_x = 10
        offset_y = 10

        # Graph widths should all fit within the graph box but have maximum width of 40

        graph_w = min(40, (max_width - (2 * offset_x)) / len(self.text.peers))

        for n, peer in enumerate(self.text.peers.values()):

            if peer.graph is not None:

                height = ((peer.count / total) * max_height) if total > 0 else 0

                x1 = (n * graph_w) + offset_x
                y1 = max_height + offset_y
                x2 = x1 + graph_w
                y2 = y1 - (int(height))
                
                self.graphs.coords(peer.graph, (x1, y1, x2, y2))

            # TODO -- Write number / name? Maybe when hovered?
                    
        self.root.update_idletasks()
        self.root.after(100, self.update_graphs)

        return

    def update_send(self):
        """ Sends any keypress information added to the queue to the server """
        try:
            while True:
                if self.push is not None and self.push.connected:
                    try:
                        self.push( self.push_queue.get_nowait() )
                    except ConnectionError:
                        return
                    self.root.update_idletasks()
                else:
                    break
        # Break when the queue is empty
        except queue.Empty:
            pass
        # Recursive call
        self.root.after(30, self.update_send)
        return

    def push_queue_put(self, messages, wait=False):
        """ Sends message to server and evaluates them locally if not other markers
            are using the same line. Use the wait flag when you want to force the
            message to go to the server and wait for the response before continuing """

        # Put message in into a list

        if isinstance(messages, MESSAGE):

            messages = [messages]

        # Messages such as mouse clicks need to wait to make sure they don't conflict with other messages

        reply = 1

        # Set reply flag and send

        for msg in messages:

            msg['reply'] = reply

            # Add the list of messages to the send queue

            self.push_queue.put(msg)
        
        return
    
    def KeyPress(self, event):
        """ 'Pushes' the key-press to the server.
        """

        # Ignore the CtrlKey and non-ascii chars

        if event.keysym in self.ignored_keys:

            return "break"

        elif event.keysym == "F4" and self.last_keypress == "Alt_L":

            self.kill()

            return "break"

        # Keep a list of messages

        messages = []

        # Get index
        
        try:

            row, col = self.text.index(self.text.marker.mark).split(".")

        except TclError as e:

            stdout("In KeyPress", e)

            stdout("My id is", self.text.marker.id)
            stdout(self.text.peers)

            return "break"

        row = int(row)
        col = int(col)

        # Un-highlight any brackets

        self.text.tag_remove("tag_open_brackets", "1.0", END)

        # If there is a change in the row number, then wait for a reply

        wait_for_reply = False

        if event.keysym == "Delete":
            
            messages.append( MSG_DELETE(self.text.marker.id, row, col) )

            wait_for_reply = True

        elif event.keysym == "BackSpace":

            # Only add a backspace if the last has been updated

            if (self.last_keypress, self.last_row, self.last_col) != ("BackSpace", row, col):

                messages.append( MSG_BACKSPACE(self.text.marker.id, row, col) )

            wait_for_reply = True

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

            if old_row != row:

                wait_for_reply = True

            messages.append( MSG_SET_MARK(self.text.marker.id, row, col) )

            # if there is some selected text, de-select

            if self.text.marker.hasSelection():

                messages.append( MSG_SELECT(self.text.marker.id, "0.0", "0.0") )

        # Inserting a character

        else:

            # Only insert a character if the current "creative constraint" is satisfied -- this is not tidy
        
            if self.__constraint__(self.text, self.text.marker):

                if event.keysym == "Return":

                    char = "\n"
                    wait_for_reply = True

                    
                elif event.keysym == "Tab":
                    
                    char = "    "
                    col += len(char)
                    
                else:
                    
                    char = event.char

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

                        messages.append( MSG_INSERT(self.text.marker.id, char, row, col) )

                    # else, move to the right one space

                    else:

                        new_row, new_col = self.Right(row, col)

                        messages.append( MSG_SET_MARK(self.text.marker.id, new_row, new_col) )

                    # Work out where the appropriate enclosing bracket is and send a message to highlight

                    loc = self.handle_bracket.find_starting_bracket(text, row, col - 1, event.char)

                    if loc is not None:

                        row1, col1 = loc
                        row2, col2 = row, col

                        messages.append( MSG_BRACKET(self.text.marker.id, row1, col1, row2, col2) )

                # Add any other character

                else:

                    messages.append( MSG_INSERT(self.text.marker.id, char, row, col) )

        # Push messages

        self.push_queue_put(messages, wait_for_reply)
            
        # Store the key info

        self.last_keypress  = event.keysym
        self.last_row       = row
        self.last_col       = col
        
        # Make sure the user sees their cursor

        self.text.see(self.text.marker.mark)
    
        return "break"

    """ Handling changes in selected areas """

    def UpdateSelect(self, last_row, last_col, new_row, new_col):
        """ Updates the currently selected portion of text for the local peer """
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

        wait_for_reply = (new_row != last_row)

        messages = [ MSG_SELECT(self.text.marker.id, start, end),
                     MSG_SET_MARK(self.text.marker.id, new_row, new_col) ]

        self.push_queue_put( messages, wait_for_reply)
                
        return "break"

    def SelectLeft(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = self.Left(row1, col1)
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"

    def SelectRight(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = self.Right(row1, col1)
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"
    
    def SelectUp(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = self.Up(row1, col1)
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"
    
    def SelectDown(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = self.Down(row1, col1)
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"

    def SelectEnd(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = (int(i) for i in self.text.index("{}.end".format(row1)).split("."))
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"

    def SelectHome(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """
        row1, col1 = self.text.index(self.text.marker.mark).split(".")
        row1, col1 = int(row1), int(col1)
        row2, col2 = (int(i) for i in self.text.index("{}.0".format(row1)).split("."))
        
        self.UpdateSelect(row1, col1, row2, col2)
        return "break"

    def SelectAll(self, event=None):
        """ Tells the server to highlight all the text in the editor and move
            the marker to 1,0 """
        start = "1.0"
        end   = self.text.index(END)

        messages = [ MSG_SELECT(self.text.marker.id, start, end),
                     MSG_SET_MARK(self.text.marker.id, 1, 0) ]

        self.push_queue_put( messages, wait=True )
                
        return "break"

    def Selection(self, event=None):
        """ Overrides handling of selected areas """
        self.text.tag_remove(SEL, "1.0", END)
        return

    """ Update colour / formatting """

    def colour_line(self, line):
        """ Embold keywords defined in Interpreter.py """

        # Get contents of the line

        start, end = "{}.0".format(line), "{}.end".format(line)
        
        string = self.text.get(start, end)

        # Go through the possible tags

        for tag_name, re_tag in self.lang.re.items():

            self.text.tag_remove(tag_name, start, end)
            
            for match in re_tag.finditer(string):
                
                tag_start = "{}.{}".format(line, match.start())
                tag_end   = "{}.{}".format(line, match.end())

                self.text.tag_add(tag_name, tag_start, tag_end)
                
        return

    """ Ctrl-Home and Ctrl-End Handling """

    def CtrlHome(self, event):

        msg = MSG_SET_MARK(self.text.marker.id, 1, 0)

        self.push_queue_put( msg, wait=True)
                
        return "break"

    def CtrlEnd(self, event):
        row, col = self.text.index(END).split(".")
        row, col = self.text.index("{}.end".format(int(row)-1)).split(".")

        msg = MSG_SET_MARK(self.text.marker.id, row, col)

        self.push_queue_put( msg, wait=True )

        self.last_keypress  = "End"
        self.last_row       = row
        self.last_col       = col
        
        return "break"

    def findWordLeft(self, row, col):
        # Go back until you find the next " "
        #index = self.text.index(self.text.marker.mark)

        if row == 1 and col == 0:

            return row, col

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

        last_row, last_col = self.text.index(self.text.marker.mark).split(".")
        last_row, last_col = int(last_row), int(last_col)

        row, col = self.findWordLeft(last_row, last_col)

        wait_for_reply = (row != last_row)

        msg = MSG_SET_MARK(self.text.marker.id, row, col)

        self.push_queue_put( msg, wait_for_reply )
                    
        return "break"

    def CtrlRight(self, event):

        last_row, last_col = self.text.index(self.text.marker.mark).split(".")
        last_row, last_col = int(last_row), int(last_col)

        row, col = self.findWordRight(last_row, last_col)

        wait_for_reply = (row != last_row)

        msg = MSG_SET_MARK(self.text.marker.id, row, col)

        self.push_queue_put( msg, wait_for_reply )
                    
        return "break"

    def findWordRight(self, row, col):

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
        """ Finds the 'block' of code that the local peer is currently in
            and returns a tuple of the start and end row """

        index = self.text.index(self.text.marker.mark)
        return self.lang.get_block_of_code(self.text, index)


    def SingleLineEvaluate(self, event=None): # TODO -- change this to single line evaluate

        # Get this line

        index = self.text.marker.index()

        row   = int(index.split(".")[0])

        a, b  = "{}.0".format(row), "{}.end".format(row)

        string = self.text.get( a , b ).lstrip()

        if string != "":

            #  Send notification to other peers

            msg = MSG_EVALUATE_BLOCK(self.text.marker.id, row, row)
            
            self.push_queue_put( msg )
        
        return "break"

    def Evaluate(self, event=None):
        """ Finds the current block of code to evaluate and tells the server """
        
        lines = self.currentBlock()
        
        a, b = ("%d.0" % n for n in lines)

        string = self.text.get( a , b ).lstrip()

        if string != "":

            #  Send notification to other peers

            msg = MSG_EVALUATE_BLOCK(self.text.marker.id, lines[0], lines[1])
            
            self.push_queue_put( msg )
                
        return "break"

    def ChangeFontSize(self, amount):
        """ Updates the font sizes of the text based on `amount` which
            can be positive or negative """
        self.root.grid_propagate(False)
        for font in self.text.font_names:
            font = tkFont.nametofont(font)
            size = max(8, font.actual()["size"] + amount)
            font.configure(size=size)
            self.text.char_w = self.text.font.measure(" ")
            self.text.char_h = self.text.font.metrics("linespace")
        return

    def DecreaseFontSize(self, event):
        """ Calls `self.ChangeFontSize(-1)` and then resizes the line numbers bar accordingly """
        self.ChangeFontSize(-1)
        self.line_numbers.config(width=self.line_numbers.winfo_width() - 2)
        # self.text.refreshPeerLabels() # -- why this doesn't work?
        return 'break'

    def IncreaseFontSize(self, event=None):
        """ Calls `self.ChangeFontSize(+1)` and then resizes the line numbers bar accordingly """
        self.ChangeFontSize(+1)
        self.line_numbers.config(width=self.line_numbers.winfo_width() + 2)
        # self.text.refreshPeerLabels()
        return 'break'

    def leftMouseRelease(self, event=None):
        """ Updates the server on where the local peer's marker is when the mouse release event is triggered """
        
        self.leftMouse_isDown = False

        index = self.text.index("@{},{}".format(event.x, event.y))
        row, col = index.split(".")
        
        self.push_queue_put( MSG_SET_MARK(self.text.marker.id, int(row), int(col)), wait=True )

        #self.text.tag_remove(SEL, "1.0", END) # Remove any *actual* selection to stop scrolling

        return "break"

    def leftMouseDrag(self, event):
        """ Updates the server with the portion of selected text """
        if self.leftMouse_isDown:
            sel_start = self.leftMouseClickIndex
            sel_end   = self.text.index("@{},{}".format(event.x, event.y))

            start, end = self.text.sort_indices([sel_start, sel_end])

            self.push_queue_put( MSG_SELECT(self.text.marker.id, start, end), wait=True )
            
        return "break"

    def leftMousePress(self, event):
        """ Updates the server on where the local peer's marker is when the mouse release event is triggered.
            Selected area is removed un-selected. """

        self.leftMouse_isDown = True

        # Get text index of click location

        self.leftMouseClickIndex = index = self.text.index("@{},{}".format( event.x, event.y ))

        row, col = index.split(".")

        # Set the mark and remove selected area

        messages = [ MSG_SET_MARK(self.text.marker.id, row, col),
                     MSG_SELECT(self.text.marker.id, "0.0", "0.0") ]

        self.push_queue_put( messages, wait=True )

        # Make sure the text box gets focus

        self.text.focus_set()        

        return "break"

    def rightMousePress(self, event):
        """ Disabled """
        return "break"

    def Undo(self, event):
        ''' Override for Ctrl+Z -- Not implemented '''
        # self.text.edit_undo()
        return "break"

    def Copy(self, event=None):
        ''' Copies selected text to the clipboard '''
        if self.text.marker.hasSelection():
            text = self.text.get(self.text.marker.sel_start, self.text.marker.sel_end)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        return "break"

    def Cut(self, event=None):
        ''' Copies selected text to the clipboard and then deletes it'''
        if self.text.marker.hasSelection():
            text = self.text.get(self.text.marker.sel_start, self.text.marker.sel_end)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            row, col = self.convert(self.text.index(self.text.marker.mark))
            self.push_queue_put( MSG_BACKSPACE(self.text.marker.id, row, col), wait=True )
        return "break"
    
    def Paste(self, event=None):
        """ Inserts text from the clipboard """
        text = self.root.clipboard_get()
        row, col = self.convert(self.text.index(self.text.marker.mark))
        self.push_queue_put( MSG_INSERT(self.text.marker.id, text, row, col), wait=True )
        return "break"

    def ToggleMenu(self, event=None):
        """ Hides or shows the menu bar """
        self.menu.toggle()
        return "break"

    def ToggleTransparency(self, event=None):
        """ Sets the text and console background to black and then removes all black pixels from the GUI """
        setting_transparent = self.transparent.get()
        if setting_transparent:
            alpha = "#000001" if SYSTEM == WINDOWS else "systemTransparent"
            self.text.config(background=alpha)
            self.line_numbers.config(background=alpha)
            self.console.config(background=alpha)
            self.graphs.config(background=alpha)
            if SYSTEM == WINDOWS:
                self.root.wm_attributes('-transparentcolor', alpha)
            else:
                self.root.wm_attributes("-transparent", True)
        else:
            self.text.config(background=COLOURS["Background"])
            self.line_numbers.config(background=COLOURS["Background"])
            self.console.config(background=COLOURS["Console"])
            self.graphs.config(background=COLOURS["Stats"])
            if SYSTEM == WINDOWS:
                self.root.wm_attributes('-transparentcolor', "")
            else:
                self.root.wm_attributes("-transparent", False)
        return

    def EditColours(self, event=None):
        """ Opens up the colour options dialog """
        from .colour_picker import ColourPicker
        ColourPicker(self)
        return

    def ApplyColours(self, event=None):
        """ Update the IDE for the new colours """ 
        LoadColours() # from config.py
        # Text & Line numbers
        self.text.config(bg=COLOURS["Background"], insertbackground=COLOURS["Background"])
        self.line_numbers.config(bg=COLOURS["Background"])
        # Console
        self.console.config(bg=COLOURS["Console"])
        # Stats
        self.graphs.config(bg=COLOURS["Stats"])
        # Peers
        for peer in self.text.peers.values():
            peer.update_colours()
            peer.configure_tags()
            self.graphs.itemconfig(peer.graph, fill=peer.bg)
        return

    def OpenGitHub(self, event=None):
        """ Opens the Troop GitHub page in the default web browser """
        webbrowser.open("https://github.com/Qirky/Troop")
        return

    def ImportLog(self):
        """ Imports a logfile generated by run-server.py --log and 'recreates' the performance """
        logname = tkFileDialog.askopenfilename()        
        self.logfile = Log(logname)
        self.logfile.set_marker(self.text.marker)
        self.logfile.recreate()
        return

    def set_interpreter(self, name):
        """ Tells Troop to interpret a new language, takes a string """
        self.lang.kill()
        self.lang=langtypes[name]()
        s = "Changing interpreted lanaguage to {}".format(repr(self.lang))
        print("\n" + "="*len(s))
        print(s)
        print("\n" + "="*len(s))
        return

    def set_constraint(self, name):
        """ Tells Troop to use a new character constraint, see `constraints.py` for more information. """
        self.push_queue_put(MSG_CONSTRAINT(self.text.marker.id, name))
        return

    def set_up_logging(self):
        """ Checks if there is a logs folder, if not this creates it """

        log_folder = os.path.join(ROOT_DIR, "logs")

        if not os.path.exists(log_folder):

            os.mkdir(log_folder)

        # Create filename based on date and times
        
        self.fn = time.strftime("client-log-%d%m%y_%H%M%S.txt", time.localtime())
        path    = os.path.join(log_folder, self.fn)
        
        self.log_file   = open(path, "w")
        self.is_logging = True
