from __future__ import absolute_import, print_function

from ..config import *
from ..message import *
from ..logfile import Log
from ..utils import *
from ..interpreter import *

from .textbox import ThreadSafeText
from .console import Console
from .peer import Peer, rgb2hex, hex2rgb
from .drag import Dragbar, ConsoleDragbar
from .bracket import BracketHandler
from .line_numbers import LineNumbers
from .menu_bar import MenuBar, PopupMenu
from .mouse import Mouse

try:
    from Tkinter import *
    import tkFileDialog
    import tkFont
    from tkColorChooser import askcolor
except ImportError:
    from tkinter import *
    from tkinter import filedialog as tkFileDialog
    from tkinter import font as tkFont
    from tkinter.colorchooser import askcolor

import os, os.path
import time
import sys
import webbrowser

ROOT = Tk()

class BasicInterface:
    """ Class for displaying basic text input data.
    """
    def __init__(self):
        self.root = ROOT
        self.root.configure(background=COLOURS["Background"])
        self.root.resizable(True, True)

        self.whitespace = (" ", "\n")
        self.delimeters = (".", ",", "(", ")", "[","]","{", "}", "=")

        self.is_logging = False
        self.logfile = None
        self.wait_msg = None
        self.waiting  = None
        self.msg_id   = 0

        # Store information about the last key pressed
        self.last_keypress  = ""
        self.last_row       = 0
        self.last_col       = 0

        self._debug_queue = []

    def run(self):
        """ Starts the Tkinter loop and exits cleanly if interrupted"""
        # Continually check for messages to be sent
        self.client.update_send()
        self.update_graphs()
        self.client.input.mainloop()
        return

    def kill(self):
        """ Terminates cleanly """
        self.root.destroy()
        return

    def reset_title(self):
        """ Overloaded in Interface class """
        return

class DummyInterface(BasicInterface):
    """ Only implemented in server debug mode """
    def __init__(self):
        BasicInterface.__init__(self)
        self.lang = DummyInterpreter()
        self.text=ThreadSafeText(self, bg=COLOURS["Background"], fg="white", insertbackground=COLOURS["Background"], height=15, bd=0)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.text.marker = Peer(-1, self.text)
        self.lang.start()

class Interface(BasicInterface):
    def __init__(self, client, title, language, logging=False):

        # Inherit

        BasicInterface.__init__(self)

        self.lang = language
        self.interpreters = {name: BooleanVar() for name in langnames}

        self.client = client

        # Set logging

        if logging:

            self.set_up_logging()

        # Set title and configure the interface grid

        self.title = title

        self.root.title(self.title)

        self.root.update_idletasks()


        self.center()

        self.root.columnconfigure(0, weight=0) # Line numbers
        self.root.columnconfigure(1, weight=2) # Text and console
        self.root.columnconfigure(2, weight=0) # Vertical dragbar
        self.root.columnconfigure(3, weight=1) # Graphs

        self.root.rowconfigure(0, weight=1) # Textbox
        self.root.rowconfigure(1, weight=0) # Dragbar
        self.root.rowconfigure(2, weight=0) # Console

        self.root.protocol("WM_DELETE_WINDOW", self.client.kill )

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
        self.using_alpha = (SYSTEM != WINDOWS)

        # Scroll bar
        self.scroll = Scrollbar(self.root)
        self.scroll.grid(row=0, column=4, sticky='nsew')

        # Text box
        self.text=ThreadSafeText(self, bg=COLOURS["Background"], fg="white", insertbackground=COLOURS["Background"],
                                    height=15, bd=0, highlightthickness=0, yscrollcommand=self.scroll.set)

        self.text.grid(row=0, column=1, sticky="nsew", columnspan=3)
        self.scroll.config(command=self.text.yview)

        # Line numbers
        self.line_numbers = LineNumbers(self.text, width=55, bg=COLOURS["Background"], bd=0, highlightthickness=0)
        self.line_numbers.grid(row=0, column=0, sticky='nsew')

        # Drag is a small line that changes the size of the console
        self.drag = Dragbar( self, bg="white", height=2  )
        self.drag.grid(row=1, column=0, stick="nsew", columnspan=4)

        # Console Box

        self.c_scroll = Scrollbar(self.root)
        self.c_scroll.grid(row=2, column=4, sticky='nsew')

        self.console = Console(self.root, bg=COLOURS["Console"], fg="white", height=5, width=50, font="Font", 
                            highlightthickness=0, yscrollcommand=self.c_scroll.set)

        self.console.grid(row=2, column=0, columnspan=2, stick="nsew")

        self.c_scroll.config(command=self.console.yview)
        
        sys.stdout = self.console # routes stdout to print to console

        self.console_drag = ConsoleDragbar(self, bg="white", width=2)
        self.console_drag.grid(row=2, column=2, stick="nsew")

        # Statistics Graphs
        self.graphs = Canvas(self.root, bg=COLOURS["Stats"], width=350, bd=0, highlightthickness=0)
        self.graphs.grid(row=2, column=3, sticky="nsew")

        # Menubar

        self.menu = MenuBar(self, visible = True)

        # Right-click menu

        self.popup = PopupMenu(self)

        # Key bindings

        CtrlKey = "Command" if SYSTEM == MAC_OS else "Control"

        # Disable by default

        disable = lambda e: "break"

        import string

        for key in list(string.digits + string.ascii_letters) + ["slash"]:

            self.text.bind("<{}-{}>".format(CtrlKey, key), disable)

        self.text.bind("escape", disable)

        # Evaluating code

        self.text.bind("<Key>", self.key_press)

        self.text.bind("<{}-Return>".format(CtrlKey), self.evaluate)
        self.text.bind("<Alt-Return>", self.single_line_evaluate)

        self.text.bind("<{}-Right>".format(CtrlKey),    self.key_ctrl_right)
        self.text.bind("<{}-Left>".format(CtrlKey),     self.key_ctrl_left)
        self.text.bind("<{}-Home>".format(CtrlKey),     self.key_ctrl_home)
        self.text.bind("<{}-End>".format(CtrlKey),      self.key_ctrl_end)
        self.text.bind("<{}-period>".format(CtrlKey),   self.stop_sound)

        self.text.bind("<{}-BackSpace>".format(CtrlKey),   self.key_ctrl_backspace)
        self.text.bind("<{}-Delete>".format(CtrlKey),      self.key_ctrl_delete)

        # indentation

        self.text.bind("<{}-bracketright>".format(CtrlKey),    self.indent)
        self.text.bind("<{}-bracketleft>".format(CtrlKey),     self.unindent)

        self.text.bind("<{}-m>".format(CtrlKey), self.menu.toggle)

        # Key bindings to handle select
        self.text.bind("<Shift-Left>",  self.select_left)
        self.text.bind("<Shift-Right>", self.select_right)
        self.text.bind("<Shift-Up>",    self.select_up)
        self.text.bind("<Shift-Down>",  self.select_down)
        self.text.bind("<Shift-End>",   self.select_end)
        self.text.bind("<Shift-Home>",  self.select_home)
        self.text.bind("<{}-a>".format(CtrlKey), self.select_all)

        # Copy and paste key bindings

        self.text.bind("<{}-c>".format(CtrlKey), self.copy)
        self.text.bind("<{}-x>".format(CtrlKey), self.cut)
        self.text.bind("<{}-v>".format(CtrlKey), self.paste)

        # # Undo
        self.text.bind("<{}-z>".format(CtrlKey), self.undo)
        self.text.bind("<{}-y>".format(CtrlKey), self.redo)

        # Handling mouse events
        self.left_mouse = Mouse(self)
        self.text.bind("<Button-1>", self.mouse_press_left)
        self.text.bind("<B1-Motion>", self.mouse_left_drag)
        self.text.bind("<ButtonRelease-1>", self.mouse_left_release)
        self.text.bind("<Double-Button-1>", self.mouse_left_double_click)
        self.text.bind("<Button-2>" if SYSTEM==MAC_OS else "<Button-3>", self.mouse_press_right)
        self.text.bind("<Button-2>" if SYSTEM!=MAC_OS else "<Button-3>", lambda *e: "break") # disable middle button

        # select_background
        self.text.tag_configure(SEL, background=COLOURS["Background"])   # Temporary fix - set normal highlighting to background colour
        self.text.bind("<<Selection>>", self.selection)

        # Allowed key-bindings

        self.text.bind("<{}-equal>".format(CtrlKey),  self.increase_font_size)
        self.text.bind("<{}-minus>".format(CtrlKey),  self.decrease_font_size)

        self.text.bind("<{}-s>".format(CtrlKey),  self.menu.save_file)
        self.text.bind("<{}-o>".format(CtrlKey),  self.menu.open_file)
        self.text.bind("<{}-n>".format(CtrlKey),  self.menu.new_file)

        self.ignored_keys = (CtrlKey + "_L", CtrlKey + "_R", "sterling", "Shift_L", "Shift_R", "Escape")

        # Directional commands

        self.directions = ("Left", "Right", "Up", "Down", "Home", "End")

        self.handle_direction = {}
        self.handle_direction["Left"]  = self.key_left
        self.handle_direction["Right"] = self.key_right
        self.handle_direction["Down"]  = self.key_down
        self.handle_direction["Up"]    = self.key_up
        self.handle_direction["Home"]  = self.key_home
        self.handle_direction["End"]   = self.key_end

        self.block_messages = False # flag to stop sending messages

        # Selection indices
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        # Set language -- TODO have knowledge of language and set boolean to True

        try:

            self.lang.start()

        except ExecutableNotFoundError as e:

            print("{}. Using Dummy Interpreter instead".format(e))

            self.lang = DummyInterpreter()

        # Set the window focus
        self.text.focus_force()

    def kill(self):
        """ Close socket connections and terminate the application """
        try:
            self.lang.kill()
            if self.logfile:
                self.logfile.stop()
            if self.is_logging:
                self.log_file.close()
        except(Exception) as e:
            stdout(e.__class__.__name__, e)
        BasicInterface.kill(self)
        return

    def freeze_kill(self, err):
        ''' Displays an error message and stops communicating to the server '''
        self.console.write(err)
        self.client.send.kill()
        self.client.recv.kill()
        return

    def center(self):

        w = 1200
        h = 900

        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()

        x = int((ws/2) - (w / 2))
        y = int((hs/2) - (h / 2))

        self.root.geometry('{}x{}+{}+{}'.format(w, h, x, y))

        # Try and start full screen (issues on Linux)

        try:

            self.root.state("zoomed")

        except TclError:

            pass

        return

    def user_disabled(self):
        """ Returns True if user is blocked from applying operations etc """
        return self.block_messages # to-do: update variable name

    @staticmethod
    def convert(index):
        """ Converts a Tkinter index into a tuple of integers """
        return tuple(int(value) for value in str(index).split("."))

    def init_local_user(self, id_num, name):
        """ Create the peer that is local to the client (text.marker) """

        try:

            self.text.marker = self.add_new_user(id_num, name)

        except ValueError:

            self.client.kill()

            print("Error: Maximum number of clients connected to server, please try again later.")

        return

    def add_new_user(self, user_id, name):
        """ Initialises a new Peer object """

        peer = self.client.peers[user_id] = Peer(user_id, name, self.text)

        # Create a bar on the graph
        peer.graph = self.graphs.create_rectangle(0,0,0,0, fill=peer.bg)

        # Draw marker

        peer.move(0)

        return peer

    def reconnect_user(self, user_id, name):
        """ Re-adds a disconnected user to the interface """
        peer = self.client.peers[user_id]
        peer.reconnect(name)
        peer.move(0)
        return peer

    def stop_sound(self, *event):
        """ Sends a kill all sound message to the server based on the language """
        self.add_to_send_queue( MSG_EVALUATE_STRING(self.text.marker.id, self.lang.stop_sound() + "\n", reply=1) )
        return "break"

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

    def sync_text(self):
        """ Re-sends the information about this client to all connected peers """
        # self.add_to_send_queue(MSG_SYNC(self.text.marker.id, self.text.handle_getall()))
        return

    # Sending messages to the server
    # ==============================

    def add_to_send_queue(self, message, wait=False):
        """ Sends message to server and evaluates them locally if not other markers
            are using the same line. Use the wait flag when you want to force the
            message to go to the server and wait for the response before continuing """

        # Call multiple times if we have a list

        if isinstance(message, list):

            for msg in message:

                self.add_to_send_queue(msg) # just in case we get nested lists somehow

        elif isinstance(message, MESSAGE):

            if self.user_disabled() is False or isinstance(message, MSG_CONNECT_ACK):

                self.msg_id += 1

                message.set_msg_id(self.msg_id)

                self.client.send_queue.put(message)

        else:

            raise TypeError("Must be MESSAGE or list")

        return

    def send_set_mark_msg(self):
        """ Sends a message to server with the location of this peer """
        self.add_to_send_queue(MSG_SET_MARK(self.text.marker.id, self.text.marker.get_index_num(), reply=0))
        return

    def send_select_msg(self):
        """ Sends a message to server with the location of this peer """
        self.add_to_send_queue(MSG_SELECT(self.text.marker.id, self.text.marker.select_start(), self.text.marker.select_end(), reply=0))
        return

    # Key press and operations
    # ========================

    def key_press(self, event):
        """ 'Pushes' the key-press to the server.
        """

        self.input_blocking = True

        # Ignore the CtrlKey and non-ascii chars

        if self.user_disabled(): # should be breaking

            self.input_blocking = False

            return "break"

        elif (event.keysym in self.ignored_keys):

            self.input_blocking = False

            return "break"

        elif event.keysym == "F4" and self.last_keypress == "Alt_L":

            self.input_blocking = False

            self.client.kill()

            return "break"

        # Get index

        index     = self.text.marker.get_index_num() # possibly just use .index_num
        line_num  = self.text.number_index_to_row_col(index)[0]
        doc_size  = len(self.text.read())
        tail      = doc_size - index
        selection = self.text.marker.selection_size()

        operation    = []
        index_offset = 0
        char         = None

        # Un-highlight any brackets

        self.remove_highlighted_brackets()

        # Key movement

        if event.keysym in self.directions:

            self.input_blocking = False

            return self.handle_direction.get(event.keysym, lambda: None).__call__()

        # Deleting a selected area

        elif selection and event.keysym in ("Delete", "BackSpace"):

            operation, index_offset = self.get_delete_selection_operation()

        # Deletion

        elif event.keysym == "Delete":

            if tail > 0:

                operation = self.new_operation(index, -1)

        elif event.keysym == "BackSpace":

            if index > 0:

                operation = self.new_operation(index - 1, -1)

                if tail > 0:

                    index_offset = -1

        # Inserting character

        elif self.text.constraint():

            if event.keysym == "Return":

                # If the line starts with blank space, add the same blank space

                char = "\n" + (" "*self.text.get_leading_whitespace(line_num))

            elif event.keysym == "Tab":

                char = " "*4

            else:

                char = event.char

            if len(char) > 0:

                if selection:

                    operation = self.new_operation(self.text.marker.select_start(), -selection, char)

                    index_offset = self.get_delete_selection_offset(char)

                else:

                    operation = self.new_operation(index, char)

                    index_offset = len(char)

        if operation:

            # Index offset is how much to *move* the label after the operation

            self.apply_operation(operation, index_offset)

            # If the character is a closing bracket, do some highlighting

            if char in self.text.right_brackets:

                self.text.highlight_brackets(char)

        # Remove any selected text

        self.de_select()

        # Store last key press for Alt+F4 etc

        self.last_keypress  = event.keysym

        self.input_blocking = False

        return "break"

    def remove_highlighted_brackets(self):
        """ Removes the text tag for highlighting brackets """
        return self.text.tag_remove("tag_open_brackets", "1.0", END)

    def new_operation(self, *ops):
        """ Returns a list of operations to apply to the document """
        return new_operation(*(list(ops) + [len(self.text.read())]))

    def get_delete_selection_operation(self):
        """ Returns an operation that deletes the selected area """
        op = self.new_operation(self.text.marker.select_start(), -self.text.marker.selection_size())
        offset = self.get_delete_selection_offset()
        return op, offset

    def get_delete_selection_offset(self, insert=""):
        """ Returns the index_offset for operations deleting the selected area. Use `insert` if you are
            inserting a character in place of the selected text """

        index = self.text.marker.get_index_num()
        sel_size = self.text.marker.selection_size()
        doc_size = len(self.text.read())

        if index == self.text.marker.select_end():
            offset = len(insert) - sel_size
        elif index == self.text.marker.select_start():
            offset = len(insert)
        else:
            raise IndexError("Selection indicies do not match")
        return offset

    def get_set_all_operation(self, text):
        """ Returns a new operation that deletes the contents then inserts the text """
        return [-len(self.text.read()), text]

    def apply_operation(self, operation, index_offset=0, **kwargs):
        """ Handles a text operation locally and sends to the server """

        if self.user_disabled() is False:

            # Apply locally

            self.text.apply_local_operation(operation, index_offset, **kwargs)

            # Handle the operation on the client side (this is just self.text.apply_client(operation) essentially)

            self.text.handle_operation(MSG_OPERATION(self.text.marker.id, operation, self.text.revision), client=True)

            # Reset the view on the textbox

            self.text.reset_view()

            # Make sure we can see the marker

            self.see_local_peer()

        return

    # Directional keypress
    # ====================

    def see_local_peer(self):
        """ Calculates the local peer tcl_index and makes sure the text widget views it """
        return self.see_peer(self.text.marker)

    def see_peer(self, peer):
        """ If the peer label (the peer's current tcl index +- 2 lines worth) is not 
            visible, make sure we can see it. """
        index        = peer.get_tcl_index()
        top_index    = "{}-2lines".format(index)
        bottom_index = "{}+2lines".format(index)
        if self.text.bbox(top_index) is None or self.text.bbox(bottom_index) is None:
            self.text.see(index)
        return

    def key_direction(self, move_func):
        """ Calls the function that moves the user's cursor then does necessary updating e.g. for server """
        self.see_local_peer()
        move_func()
        self.send_set_mark_msg()
        self.de_select()
        self.see_local_peer()
        return "break"

    def key_left(self):
        """ Called when the left arrow key is pressed; decreases the local peer index
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_left)

    def key_right(self):
        """ Called when the right arrow key is pressed; increases the local peer index
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_right)

    def key_down(self):
        """ Called when the down arrow key is pressed; increases the local peer index
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_down)

    def key_up(self):
        """ Called when the up arrow key is pressed; decrases the local peer index
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_up)

    def key_home(self):
        """ Called when the home key is pressed; sets the local peer location to 0
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_home)

    def key_end(self):
        """ Called when the home key is pressed; sets the local peer location to 0
            and updates the location of the label then sends a message to the server
            with the new location """
        return self.key_direction(self.move_marker_end)

    def key_ctrl_home(self, event):
        """ Called when the user pressed Ctrl+Home. Sets the local peer index to 0 """
        return self.key_direction(self.move_marker_ctrl_home)

    def key_ctrl_end(self, event):
        """ Called when the user pressed Ctrl+End. Sets the local peer index to the end of the document """
        return self.key_direction(self.move_marker_ctrl_end)

    def key_ctrl_left(self, event):
        """ Called when the user pressed Ctrl+Left. Sets the local peer index to left of the previous word """
        return self.key_direction(self.move_marker_ctrl_left)

    def key_ctrl_right(self, event):
        """ Called when the user pressed Ctrl+Left. Sets the local peer index to right of the next word """
        return self.key_direction(self.move_marker_ctrl_right)

    # Deleting multiple characters

    def key_ctrl_backspace(self, event):
        """ Uses Ctrl+Left to move marker and delete the characters between """
        if self.text.marker.has_selection():
            op, offset = self.get_delete_selection_operation()
            self.de_select()
        else:
            index, _, new = self.text.marker.get_index_num(), self.move_marker_ctrl_left(), self.text.marker.get_index_num()
            if index == 0: # don't apply operation if we are at the start
                return "break"
            op, offset = self.new_operation(new, new - index), 0
        self.apply_operation(op, offset)
        return "break"

    def key_ctrl_delete(self, event):
        """ Uses Ctrl+Right to move marker and then delete the characters between """
        if self.text.marker.has_selection():
            op, offset = self.get_delete_selection_operation()
            self.de_select()
        else:
            len_text = len(self.text.read())
            index, _, new = self.text.marker.get_index_num(), self.move_marker_ctrl_right(), self.text.marker.get_index_num()
            if len_text == 0: # dont apply operation if there is no text
                return "break"
            op = self.new_operation(index, index - new)
            if new == len_text:
                offset = 0
            else:
                offset = index - new
        self.apply_operation(op, offset)
        return "break"


    # Moving the text marker
    # ======================

    def move_marker_left(self):
        """ Move the cursor right 1 place """
        self.text.marker.shift(-1)

    def move_marker_right(self):
        """ Move the cursor right 1 place """
        self.text.marker.shift(+1)

    def move_marker_up(self):
        """ Move the  cursor one line down """
        tcl_index  = self.text.number_index_to_tcl(self.text.marker.get_index_num())
        line_num   = int(tcl_index.split(".")[0])
        # Use the bounding box to adjust the y-pos
        # self.text.see(tcl_index)
        x, y, w, h = self.text.bbox(tcl_index)
        y = y - h
        # If the new index is off the canvas, try and see the line
        if y < 0:
            self.text.see(tcl_index + "-1lines")
            x, y, w, h = self.text.bbox(tcl_index)
            y = y - h
        if y > 0:
            new_index = self.text.tcl_index_to_number( self.text.index("@{},{}".format(x, y)) )
            self.text.marker.move(new_index)
        return

    def move_marker_down(self):
        """ Move the marker one line down """
        tcl_index = self.text.number_index_to_tcl(self.text.marker.get_index_num())
        # Use the bounding box to adjust the y-pos
        x, y, w, h = self.text.bbox(tcl_index)
        # If the line down is off screen, make sure we can see it
        if (y + (2 * h)) >= self.text.winfo_height():
            self.text.see(tcl_index + "+1lines") # View lines we can't see
        # Calculate new index and check bbox
        new_tcl_index = self.text.index("@{},{}".format(x, y + h))
        _, y1, _, _ = self.text.bbox(new_tcl_index)
        # Only move if the new line is different
        if y != y1:
            new_index = self.text.tcl_index_to_number( new_tcl_index )
            self.text.marker.move(new_index)
        return

    def move_marker_home(self):
        """ Moves the cursor to the beginning of a line """
        tcl_index = self.text.number_index_to_tcl(self.text.marker.get_index_num())
        x, y, w, h = self.text.bbox(tcl_index)
        index = self.text.tcl_index_to_number( self.text.index("@{},{}".format(1, y)) )
        self.text.marker.move(index)
        return

    def move_marker_end(self):
        """ Moves the cursor to the end of a line """
        tcl_index = self.text.number_index_to_tcl(self.text.marker.get_index_num())
        x, y, w, h = self.text.bbox(tcl_index)
        new_x = self.text.winfo_width()
        index = self.text.tcl_index_to_number( self.text.index("@{},{}".format(new_x, y)) ) # TODO: This goes one char short?
        self.text.marker.move(index)
        return

    def move_marker_ctrl_home(self):
        """ Moves the cursor the beginning of the document """
        self.text.marker.move(0)
        return

    def move_marker_ctrl_end(self):
        """ Moves the cursor to the end of the document """
        self.text.marker.move(len(self.text.read()))
        return

    def move_marker_ctrl_left(self):
        """ Moves the cursor to the start of the current word"""
        index = self.get_word_left_index(self.text.marker.get_index_num())
        self.text.marker.move(index)
        return

    def move_marker_ctrl_right(self):
        """ Moves the cursor to the end of the current word, or next word if we are at the end.
            Left must be non-space, and right must be space"""
        index = self.get_word_right_index(self.text.marker.get_index_num())
        self.text.marker.move(index)
        return

    def get_word_left_index(self, index):
        """ Returns the index of the start of the current word """
        text  = self.text.read()
        # Don't look at the character before if it's a delimeter
        if index > 0 and text[index - 1] in (self.delimeters + self.whitespace):
            index -= 1
        for i in range(index, 0, -1):
            if text[i - 1] in self.delimeters and text[i] in self.delimeters:
                break
            elif text[i - 1] in (self.delimeters + self.whitespace) and text[i] not in (self.delimeters + self.whitespace):
                break
        else:
            i = 0
        return i

    def get_word_right_index(self, index):
        """ Returns the index of the end of the current word """
        text  = self.text.read()
        if index < len(text) and text[index] in (self.delimeters + self.whitespace):
            index += 1
        for i in range(index, len(text) - 1):
            if text[i - 1] in self.delimeters and text[i] in self.delimeters:
                break
            elif text[i - 1] not in (self.delimeters + self.whitespace) and text[i] in (self.delimeters + self.whitespace):
                break
        else:
            i = len(text)
        return i
        

    # Selection handling
    # ==================

    def de_select(self):
        """ If there is a selection, remove it and notify the server """
        notify = self.text.marker.de_select()
        if notify:
            self.send_select_msg()
        return

    def get_movement_index(self, move_func):
        """ Calls `move_func` and returns the index of the marker before and after the call """
        assert callable(move_func)
        start, _, end = self.text.marker.get_index_num(), move_func(), self.text.marker.get_index_num()
        return start, end

    def update_select(self, start, end):
        """ Updates the current selected area """

        # Update the selection
        self.text.marker.select(start, end)

        # Send info to server
        self.send_set_mark_msg()
        self.send_select_msg()

        # Update colours
        self.text.update_colours()

        return

    def select_left(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_left) )

        return "break"

    def select_right(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """
            
        self.update_select( *self.get_movement_index(self.move_marker_right) )

        return "break"

    def select_up(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_up) )

        return "break"

    def select_down(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_down) )

        return "break"

    def select_end(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_end) )

        return "break"

    def select_home(self, event):
        """ Finds the currently selected portion of text of the local peer
            and the row/col to update it to and calls self.UpdateSelect  """

        self.update_select( *self.get_movement_index(self.move_marker_home) )

        return "break"

    def select_all(self, event=None):
        """ Tells the server to highlight all the text in the editor and move
            the marker to 1,0 """

        self.text.marker.move(0)
        self.update_select(0, len(self.text.read()))

        return "break"

    def selection(self, event=None):
        """ Overrides handling of selected areas """
        self.text.tag_remove(SEL, "1.0", END)
        return

    # Evaluating lines
    # ================

    def get_current_block(self):
        """ Finds the 'block' of code that the local peer is currently in
            and returns a tuple of the start and end row """
        return self.lang.get_block_of_code(self.text, self.text.marker.get_tcl_index())


    def single_line_evaluate(self, event=None):
        """ Finds contents of the current line and sends a message to each user (inc. this one) to evaluate """

        if self.input_blocking:

            # schedule

            self.after(50, lambda: self.evaluate(event))

        else:

            row, _ = self.text.number_index_to_row_col(self.text.marker.get_index_num())
            a, b   = "{}.0".format(row), "{}.end".format(row)

            if self.text.get(a, b).lstrip() != "":

                self.add_to_send_queue( MSG_EVALUATE_BLOCK(self.text.marker.id, row, row) )

        return "break"

    def evaluate(self, event=None):
        """ Finds the current block of code to evaluate and tells the server """

        if self.input_blocking:

            # schedule

            self.after(50, lambda: self.evaluate(event))

        else:

            lines = self.get_current_block()

            a, b = ("%d.0" % n for n in lines)

            string = self.text.get( a , b ).lstrip()

            if string != "":

                #  Send notification to other peers

                msg = MSG_EVALUATE_BLOCK(self.text.marker.id, lines[0], lines[1])

                self.add_to_send_queue( msg )

        return "break"

    # Font size
    # =========

    def change_font_size(self, amount):
        """ Updates the font sizes of the text based on `amount` which
            can be positive or negative """
        self.root.grid_propagate(False)
        for font in self.text.font_names:
            font = tkFont.nametofont(font)
            size = font.actual()["size"] + amount
            if size >= 8:

                font.configure(size=size)

                self.text.char_w = self.text.font.measure(" ")
                self.text.char_h = self.text.font.metrics("linespace")

                shift = 2 * (1 if amount > 0 else -1)

                self.line_numbers.config(width=self.line_numbers.winfo_width() + shift)

        return

    def decrease_font_size(self, event):
        """ Calls `self.ChangeFontSize(-1)` and then resizes the line numbers bar accordingly """
        self.change_font_size(-1)
        return 'break'

    def increase_font_size(self, event=None):
        """ Calls `self.ChangeFontSize(+1)` and then resizes the line numbers bar accordingly """
        self.change_font_size(+1)
        return 'break'

    # Mouse Clicks
    # ============

    def mouse_press_left(self, event):
        """ Updates the server on where the local peer's marker is when the mouse release event is triggered.
            Selected area is removed un-selected. """

        # If we click somewhere, remove the closed brackets tag

        self.remove_highlighted_brackets() 

        # Get location and process

        index = self.left_mouse.click(event)

        self.text.marker.move(index)

        self.de_select()

        self.add_to_send_queue( MSG_SET_MARK(self.text.marker.id, index) )

        # Make sure the text box gets focus

        self.text.focus_set()

        return "break"

    def mouse_left_release(self, event=None):
        """ Updates the server on where the local peer's marker is when the mouse release event is triggered """

        index = self.left_mouse.release(event)

        self.text.marker.move(index)

        self.add_to_send_queue( MSG_SET_MARK(self.text.marker.id, index) )

        # Make sure the text box gets focus

        self.text.focus_set()

        #self.text.tag_remove(SEL, "1.0", END) # Remove any *actual* selection to stop scrolling

        return "break"

    def mouse_left_drag(self, event):
        """ Updates the server with the portion of selected text """
        if self.left_mouse.is_pressed:

            start = self.left_mouse.anchor
            end   = self.left_mouse.click(event)

            self.update_select(start, end) # sends message to server

        return "break"

    def mouse_left_double_click(self, event):
        """ Highlights word - not yet implemented """
        index = self.left_mouse.click(event)
        right = self.get_word_right_index(index)
        left  = self.get_word_left_index(index)
        self.update_select(left, right)
        return "break"

    def mouse_press_right(self, event):
        """ Displays popup menu"""
        self.popup.show(event)
        return "break"

    # Copy, paste, undo etc
    # =====================

    def undo(self, event=None):
        ''' Triggers an undo event '''
        if len(self.text.undo_stack):
            op = self.text.get_undo_operation()
            self.apply_operation(self.new_operation(*op.ops), index=get_operation_index(op.ops), undo=True)
        return "break"

    def redo(self, event=None):
        ''' Re-applies the last undo event '''
        if len(self.text.redo_stack):
            op = self.text.get_redo_operation()
            self.apply_operation(self.new_operation(*op.ops), index=get_operation_index(op.ops), redo=True)
        return "break"

    def copy(self, event=None):
        ''' Copies selected text to the clipboard '''
        if self.text.marker.has_selection():
            text = self.text.read()[self.text.marker.select_start():self.text.marker.select_end()]
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        return "break"

    def cut(self, event=None):
        ''' Copies selected text to the clipboard and then deletes it'''
        if self.text.marker.has_selection():
            text = self.text.read()[self.text.marker.select_start():self.text.marker.select_end()]

            self.root.clipboard_clear()
            self.root.clipboard_append(text)

            start_point = self.text.marker.select_start()

            operation = self.new_operation(start_point, -self.text.marker.selection_size())

            self.apply_operation(operation)

            self.de_select()

            self.text.marker.move(start_point)

        return "break"

    def paste(self, event=None):
        """ Inserts text from the clipboard """

        try:

            text = self.root.clipboard_get()

        except TclError:

            return "break"

        if len(text):

            # If selected, delete that first
            if self.text.marker.has_selection():

                selection = self.text.marker.selection_size()

                operation = self.new_operation(self.text.marker.select_start(), -selection, text)

                offset = self.get_delete_selection_offset(text)

                self.apply_operation(operation, index_offset=offset)

                self.de_select()

            else:

                operation = self.new_operation(self.text.marker.get_index_num(), text)

                self.apply_operation(operation, index_offset=len(text))

        return "break"

    def indent(self, event=None):
        return "break"

    def unindent(self, event=None):
        return "break"

    # Interface toggles
    # =================

    def toggle_transparency(self, event=None):
        """ Sets the text and console background to black and then removes all black pixels from the GUI """
        setting_transparent = self.transparent.get()
        if setting_transparent:
            if not self.using_alpha:
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
                self.root.wm_attributes("-alpha", float(COLOURS["Alpha"]))
        else:
            # Re-use colours
            if not self.using_alpha:
                self.text.config(background=COLOURS["Background"])
                self.line_numbers.config(background=COLOURS["Background"])
                self.console.config(background=COLOURS["Console"])
                self.graphs.config(background=COLOURS["Stats"])
                if SYSTEM == WINDOWS:
                    self.root.wm_attributes('-transparentcolor', "")
                else:
                    self.root.wm_attributes("-transparent", False)
            else:
                self.root.wm_attributes("-alpha", 1)
        return

    # Colour scheme changes
    # =====================

    def edit_colours(self, event=None):
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

    # Misc.
    # =====

    def OpenGitHub(self, event=None):
        """ Opens the Troop GitHub page in the default web browser """
        webbrowser.open("https://github.com/Qirky/Troop")
        return

    def set_interpreter(self, name):
        """ Tells Troop to interpret a new language, takes a string """
        self.lang.kill()

        try:
            self.lang=langtypes[name](self.client.args)

        except ExecutableNotFoundError as e:

            print(e)

            self.lang = DummyInterpreter()

        s = "Changing interpreted lanaguage to {}".format(repr(self.lang))
        print("\n" + "="*len(s))
        print(s)
        print("\n" + "="*len(s))

        self.lang.start()

        return

    def set_constraint(self, name):
        """ Tells Troop to use a new character constraint, see `constraints.py` for more information. """
        self.add_to_send_queue(MSG_CONSTRAINT(self.text.marker.id, name))
        return

    # Message logging
    # ===============

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

    def log_message(self, message):
        """ Logs a message to the widget's log_file with a timestamp """
        self.log_file.write("%.4f" % time.time() + " " + repr(str(message)) + "\n")
        return

    def ImportLog(self):
        """ Imports a logfile generated by run-server.py --log and 'recreates' the performance """
        logname = tkFileDialog.askopenfilename()
        self.logfile = Log(logname)
        self.logfile.set_marker(self.text.marker)
        self.logfile.recreate()
        return
