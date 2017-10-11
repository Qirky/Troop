from __future__ import absolute_import

try:
    from Tkinter import Menu
except ImportError:
    from tkinter import Menu
    
from functools import partial

from ..config import *

class MenuBar(Menu):
    def __init__(self, master, visible=True):

        self.root = master

        Menu.__init__(self, master.root)

        # File menu

        filemenu = Menu(self, tearoff=0)
        filemenu.add_command(label="New Document",  command=lambda: "break",   accelerator="Ctrl+N")
        filemenu.add_command(label="Save",          command=lambda: "break",   accelerator="Ctrl+S")
        filemenu.add_command(label="Save As...",    command=lambda: "break" )
        filemenu.add_separator()
        filemenu.add_command(label="Start logging performance", command=lambda: "break")
        filemenu.add_command(label="Import logged performance", command=self.root.ImportLog)
        self.add_cascade(label="File", menu=filemenu)

        # Edit menu

        editmenu = Menu(self, tearoff=0)
        editmenu.add_command(label="Cut",        command=self.root.Cut,   accelerator="Ctrl+X")
        editmenu.add_command(label="Copy",       command=self.root.Copy,  accelerator="Ctrl+C")
        editmenu.add_command(label="Paste",      command=self.root.Paste, accelerator="Ctrl+V")
        editmenu.add_command(label="Select All", command=self.root.SelectAll,  accelerator="Ctrl+/")
        editmenu.add_separator()
        editmenu.add_command(label="Increase Font Size",      command=self.root.IncreaseFontSize, accelerator="Ctrl+=")
        editmenu.add_command(label="Decrease Font Size",      command=self.root.DecreaseFontSize, accelerator="Ctrl+-")
        editmenu.add_separator()
        editmenu.add_command(label="Toggle Menu", command=self.root.ToggleMenu, accelerator="Ctrl+M")
        editmenu.add_separator()
        editmenu.add_command(label="Edit Colours", command=self.root.EditColours)
        self.add_cascade(label="Edit", menu=editmenu)

        # Code menu

        codemenu = Menu(self, tearoff=0)
        codemenu.add_command(label="Evaluate Code",         command=self.root.Evaluate,        accelerator="Ctrl+Return")
        codemenu.add_command(label="Evaluate Code Locally", command=self.root.LocalEvaluate,   accelerator="Alt+Return")
        codemenu.add_command(label="Stop All Sound",        command=self.root.stopSound,       accelerator="Ctrl+.")
        editmenu.add_separator()

        # Allow choice of interpreter
        langmenu = Menu(self, tearoff=0)

        for name, interpreter in langnames.items():

            langmenu.add_checkbutton(label=name.title(),
                                     command  = partial(self.root.set_interpreter, interpreter),
                                     variable = self.root.interpreters[name])
            
        codemenu.add_cascade(label="Choose language", menu=langmenu)
        
        self.add_cascade(label="Code", menu=codemenu)

        # Creative constraint menu

        constraintmenu = Menu(self, tearoff=0)

        # Get the names of constraints

        from . import constraints
        constraints = vars(constraints)

        for name in constraints:

            if not name.startswith("_"):

                constraintmenu.add_checkbutton(label=name.title(),
                                           command  = partial(self.root.set_constraint, name),
                                           variable = self.root.creative_constraints[name])

        self.add_cascade(label="Constraints", menu=constraintmenu)        

        # Help

        helpmenu = Menu(self, tearoff=0)
        helpmenu.add_command(label="Documentation",   command=self.root.OpenGitHub)
        self.add_cascade(label="Help", menu=helpmenu)

        # Add to root

        self.visible = visible
        
        if self.visible:
            
            master.root.config(menu=self)

    def toggle(self):
        self.root.root.config(menu=self if not self.visible else 0)
        self.visible = not self.visible
        return
