from __future__ import absolute_import

try:
    from Tkinter import *
    from tkColorChooser import askcolor
except ImportError:
    from tkinter import *
    from tkinter.colorchooser import askcolor
    
from ..config import *

"""
Widget that assigns background and Peer IDs a specific colour
"""

class ColourPicker(Frame):
    def __init__(self, master):
        self.master = master
        self.root=Toplevel(master.root)
        self.root.title("Edit Colours")
        self.root.attributes('-topmost', 'true')

        self.filename=COLOUR_INFO_FILE
        
        self.attributes = ["Background", "Console"] + ["Peer {}".format(n) for n in range(1,11)]

        # load in colours 
        self.colours = self.read()
        self.labels  = {}
        self.selected = IntVar(value=0)

        for i, name in enumerate(self.attributes):
            # Make a button to trigger colour picker
            lbl = Radiobutton(self.root, text=name, width=10,
                              indicatoron=0,
                              variable=self.selected, value=i,
                              command=lambda: self.get_colour())
            lbl.grid(row=i, column=0)
            
            # Make a label for showing the colour
            lbl = Label(self.root, bg=self.colours[name], width=15)
            lbl.grid(row=i, column=1)
            self.labels[name] = lbl
            
        # Make a save changes button
        b = Button(self.root, text="Save Changes", command=self.write)
        b.grid(row=i+1, column=0, columnspan=2, stick="nsew")

    def get_colour(self):
        """ Opens a colour palette dialog """
        attr=self.attributes[self.selected.get()]
        rgb, html = askcolor(color=self.colours[attr])
        if rgb != None:
            self.colours[attr] = html
            self.labels[attr].config(bg=html)
        return

    def write(self):
        """ Writes to file """
        with open(self.filename, "w") as f:
            for attr in self.attributes:
                f.write("{}={}\n".format(attr, self.colours[attr]))
        self.master.ApplyColours()
        return

    def read(self):
        """ Reads from file """
        data = {}
        data["Background"] = COLOURS["Background"]
        data["Console"]    = COLOURS["Console"]
        for n in range(10):
            data["Peer {}".format(n + 1)] = COLOURS["Peers"][n]
        return data
