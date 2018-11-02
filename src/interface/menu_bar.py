from __future__ import absolute_import

try:
    from Tkinter import Menu, DISABLED, NORMAL, StringVar
    import tkFileDialog
    import tkMessageBox
except ImportError:
    from tkinter import Menu, DISABLED, NORMAL, StringVar
    from tkinter import filedialog as tkFileDialog
    from tkinter import messagebox as tkMessageBox
    
from functools import partial

from ..config import *
from ..message import *

class MenuBar(Menu):
    def __init__(self, master, visible=True):

        self.root = master

        Menu.__init__(self, master.root)

        # File menu

        filemenu = Menu(self, tearoff=0)
        filemenu.add_command(label="New Document",  command=self.new_file,   accelerator="Ctrl+N")
        filemenu.add_command(label="Save",          command=self.save_file,   accelerator="Ctrl+S")
        filemenu.add_command(label="Open",          command=self.open_file,   accelerator="Ctrl+O")
        filemenu.add_separator()
        filemenu.add_command(label="Start logging performance", command=lambda: "break")
        filemenu.add_command(label="Import logged performance", command=self.root.ImportLog)
        self.add_cascade(label="File", menu=filemenu)

        # Edit menu

        editmenu = Menu(self, tearoff=0)
        editmenu.add_command(label="Cut",        command=self.root.cut,   accelerator="Ctrl+X")
        editmenu.add_command(label="Copy",       command=self.root.copy,  accelerator="Ctrl+C")
        editmenu.add_command(label="Paste",      command=self.root.paste, accelerator="Ctrl+V")
        editmenu.add_command(label="Select All", command=self.root.select_all,  accelerator="Ctrl+/")
        editmenu.add_separator()
        editmenu.add_command(label="Increase Font Size",      command=self.root.increase_font_size, accelerator="Ctrl+=")
        editmenu.add_command(label="Decrease Font Size",      command=self.root.decrease_font_size, accelerator="Ctrl+-")
        editmenu.add_separator()
        editmenu.add_command(label="Toggle Menu", command=self.toggle, accelerator="Ctrl+M")
        editmenu.add_separator()
        editmenu.add_command(label="Edit Colours", command=self.root.edit_colours)
        editmenu.add_checkbutton(label="Toggle Window Transparency",  command=self.root.toggle_transparency, variable=self.root.transparent)
        self.add_cascade(label="Edit", menu=editmenu)

        # Code menu

        codemenu = Menu(self, tearoff=0)
        codemenu.add_command(label="Evaluate Code",         command=self.root.evaluate,        accelerator="Ctrl+Return")
        codemenu.add_command(label="Evaluate Single Line",  command=self.root.single_line_evaluate,   accelerator="Alt+Return")
        codemenu.add_command(label="Stop All Sound",        command=self.root.stop_sound,       accelerator="Ctrl+.")
        codemenu.add_command(label="Font colour merge",     command=self.root.text.merge.start)

        # Constraints

        constmenu = Menu(self, tearoff=0)

        for i, name in self.root.text.constraint.items():

            constmenu.add_checkbutton(label=str(name).title(),
                                      command  = partial(self.root.set_constraint, i),
                                      variable = self.root.text.constraint.using[i])
            
        codemenu.add_cascade(label="Set Constraint", menu=constmenu)

        codemenu.add_separator()

        # Allow choice of interpreter

        langmenu = Menu(self, tearoff=0)

        for name, interpreter in langnames.items():

            langmenu.add_checkbutton(label=langtitles[name],
                                     command  = partial(self.root.set_interpreter, interpreter),
                                     variable = self.root.interpreters[name])
            
        codemenu.add_cascade(label="Choose language", menu=langmenu)
        
        self.add_cascade(label="Code", menu=codemenu)

        # Help

        helpmenu = Menu(self, tearoff=0)
        helpmenu.add_command(label="Documentation",   command=self.root.OpenGitHub)
        self.add_cascade(label="Help", menu=helpmenu)

        # Add to root

        self.visible = visible
        
        if self.visible:
            
            master.root.config(menu=self)

    def toggle(self, *args, **kwargs):
        self.root.root.config(menu=self if not self.visible else 0)
        self.visible = not self.visible
        return "break"

    def save_file(self, event=None):
        """ Opens a save file dialog """
        lang_files = ("{} file".format(repr(self.root.lang)), self.root.lang.filetype )
        all_files = ("All files", "*.*")
        fn = tkFileDialog.asksaveasfilename(title="Save as...", filetypes=(lang_files, all_files), defaultextension=lang_files[1])
        if len(fn):
            with open(fn, "w") as f:
                f.write(self.root.text.read())
            print("Saved: {}".format(fn))
        return

    def new_file(self, event=None):
        """ Asks if the user wants to clear the screen and does so if yes """
        return

    def open_file(self, event=None):
        """ Opens a fileopen dialog then sets the text box contents to the contents of the file """
        lang_files = ("{} files".format(repr(self.root.lang)), self.root.lang.filetype )
        all_files = ("All files", "*.*")
        fn = tkFileDialog.askopenfilename(title="Open file", filetypes=(lang_files, all_files))
        
        if len(fn):

            with open(fn) as f:
                contents = f.read()

            self.root.apply_operation( self.root.get_set_all_operation(contents) )

        return


class PopupMenu(Menu):
    def __init__(self, master):
        self.root = master
        Menu.__init__(self, master.root, tearoff=0, postcommand=self.update)
        self.add_command(label="Undo", command=self.root.undo, accelerator="Ctrl+Z") 
        self.add_command(label="Redo", command=self.root.redo, accelerator="Ctrl+Y")
        self.add_separator()
        self.add_command(label="Copy", command=self.root.copy, accelerator="Ctrl+C")
        self.add_command(label="Cut", command=self.root.cut, accelerator="Ctrl+X")
        self.add_command(label="Paste", command=self.root.paste, accelerator="Ctrl+V")
        self.add_separator()
        self.add_command(label="Select All", command=self.root.select_all, accelerator="Ctrl+A")

        self.bind("<FocusOut>", self.hide) # hide when clicked off

    def is_active(self):
        return self.active

    def show(self, event):
        """ Displays the popup menu """
        self.focus_set()
        return self.post(event.x_root, event.y_root)

    def hide(self, event=None):
        """ Removes the display of the popup """
        return self.unpost()

    def update(self):
        """ Sets the state for variables"""

        self.entryconfig("Undo", state=NORMAL if len(self.root.text.undo_stack) > 0 else DISABLED)
        self.entryconfig("Redo", state=NORMAL if len(self.root.text.redo_stack) > 0 else DISABLED)

        select = self.root.text.marker.has_selection()
        self.entryconfig("Copy", state=NORMAL if select else DISABLED)
        self.entryconfig("Cut", state=NORMAL if select else DISABLED)

        return

class ConsolePopupMenu(PopupMenu):
    def __init__(self, master):
        self.root = master # console widget
        disable = lambda *e: None
        Menu.__init__(self, master.root, tearoff=0, postcommand=self.update)
        self.add_command(label="Undo", command=disable, accelerator="Ctrl+Z", state=DISABLED) 
        self.add_command(label="Redo", command=disable, accelerator="Ctrl+Y", state=DISABLED)
        self.add_separator()
        self.add_command(label="Copy", command=self.root.copy, accelerator="Ctrl+C")
        self.add_command(label="Cut", command=disable, accelerator="Ctrl+X", state=DISABLED)
        self.add_command(label="Paste", command=disable, accelerator="Ctrl+V", state=DISABLED)
        self.add_separator()
        self.add_command(label="Select All", command=self.root.select_all, accelerator="Ctrl+A")

        self.bind("<FocusOut>", self.hide) # hide when clicked off

    def update(self):
        self.entryconfig("Copy", state=NORMAL if self.root.has_selection() else DISABLED)
        return