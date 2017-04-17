from  Tkinter import *
from ..config import *
import Queue
import re

re_colour = re.compile(r"<colour=\"(?P<colour>.*?)\">(?P<c_text>.*?)</colour>(?P<string>.*?)$", re.DOTALL)

def find_colour(string):
    return re_colour.search(string)

class Console(Text):
    def __init__(self, root, **kwargs):
        # Inherit
        Text.__init__(self, root, **kwargs)       

        # Queue waits for messages to be added to the console
        self.queue = Queue.Queue()

        # Don't allow keypresses
        self.bind("<Key>", self.null)

        self.colours = {}

        self.update_me()

    def null(self, event):
        return "break"

    def update_me(self):
        try:
            while True:
                
                string = self.queue.get_nowait().strip()
                
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

        except Queue.Empty:

            pass
        
        self.after(100, self.update_me)

    def write(self, string):        
        if string != "\n":
            self.queue.put(string)
        return
        
