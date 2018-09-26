from __future__ import absolute_import
from ..config import *

try:
    from Tkinter import *
    import tkFont
except ImportError:
    from tkinter import *
    from tkinter import font as tkFont

try:
    import queue
except ImportError:
    import Queue as queue

from .menu_bar import ConsolePopupMenu

import re

re_colour = re.compile(r"<colour=\"(?P<colour>.*?)\">(?P<c_text>.*?)</colour>(?P<string>.*?)$", re.DOTALL)

def find_colour(string):
    return re_colour.search(string)

class Console(Text):
    def __init__(self, root, **kwargs):
        # Inherit
        Text.__init__(self, root, **kwargs)

        self.root = root # 

        # Set font

        if SYSTEM == MAC_OS:

            fontfamily = "Monaco"

        elif SYSTEM == WINDOWS:

            fontfamily = "Consolas"

        else:

            fontfamily = "Courier New"

        self.font = tkFont.Font(family=fontfamily, size=12, name="ConsoleFont")
        self.font.configure(**tkFont.nametofont("ConsoleFont").configure())

        self.configure(font="ConsoleFont")

        # Queue waits for messages to be added to the console
        self.queue = queue.Queue()

        # By default, don't allow keypresses
        self.bind("<Key>", self.null)
        
        self.bind("<Button-2>" if SYSTEM==MAC_OS else "<Button-3>", self.mouse_press_right)

        CtrlKey = "Command" if SYSTEM == MAC_OS else "Control"

        self.bind("<{}-c>".format(CtrlKey), self.copy)
        self.bind("<{}-a>".format(CtrlKey), self.select_all)

        self.popup = ConsolePopupMenu(self)

        self.colours = {}

        self.update_me()

    def null(self, event):
        return "break"

    def update_me(self):
        try:
            while True:
                
                string = self.queue.get_nowait().rstrip() # Remove trailing whitespace
                
                match = find_colour(string)

                if match:

                    self.mark_set(INSERT, END)

                    colour = match.group("colour")
                    c_text = match.group("c_text")
                    string = match.group("string")

                    start = self.index(INSERT)
                    self.insert(INSERT, c_text)
                    end   = self.index(INSERT)

                    # Add tag

                    if colour not in self.colours:

                        self.colours[colour] = "tag_%s" % colour

                        self.tag_config(self.colours[colour], foreground=colour)

                    self.tag_add(self.colours[colour], start, end)

                self.insert(END, string + "\n")

                self.see(END)

                self.update_idletasks()

        except queue.Empty:

            pass
        
        self.after(100, self.update_me)

    def write(self, string):        
        """ Adds a string to the console queue """
        if string != "\n":
            self.queue.put(string)
        return

    def flush(self, *args, **kwargs):
        """ Override """
        return

    def has_selection(self):
        """ Returns True if the SEL tag is found in the Console widget """
        return bool(self.tag_ranges(SEL))

    def get_selection(self):
        return self.get(SEL_FIRST, SEL_LAST)

    def mouse_press_right(self, event):
        """ Displays popup menu"""
        self.popup.show(event)
        return "break"

    def copy(self, event=None):
        if self.has_selection():
            self.root.clipboard_clear()
            self.root.clipboard_append(self.get_selection())
        return "break"

    def select_all(self, event=None):
        self.tag_add(SEL,"1.0", END)
        return "break"
