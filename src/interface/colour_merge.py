try:
    from Tkinter import *
    from tkColorChooser import askcolor
except ImportError:
    from tkinter import *
    from tkinter.colorchooser import askcolor

class ColourMerge(object):
    """docstring for ColourMerge"""
    def __init__(self, parent, *args, **kwargs):
        self.parent       = parent # text widget
        self.colour       = None
        self.duration     = 0
        self.time_elapsed = 0
        self.recur_time   = 0
        self.weight       = 0

    def start(self, event=None):
        """ Opens a basic text-entry window and starts the process of "merging fonts".
            This is the slow process of converging all the font colours to the same
            colour. 
        """

        # TODO get values from a window

        _, self.colour = askcolor()
        self.duration  = self.ask_duration()

        self.recur_time = int( (60000 * self.duration) / 100)

        self.update_font_colours(recur_time = self.recur_time )

        return

    def ask_duration(self):
        """ Opens a small window that asks the user to enter a duration """

        self.root         = self.parent.root.root # Tk instance
        
        popup = popup_window(self.root, title="Set duration")
        popup.text.focus_set()

        # Put the popup on top
        
        self.root.wait_window(popup.top)

        return float(popup.value)

        
    def update_font_colours(self, recur_time=0):
        """ Updates the font colours of all the peers. Set a recur time
            to update reguarly. 
        """

        for peer in self.parent.peers.values():

            peer.update_colours()
            
            peer.configure_tags()
            
            self.parent.root.graphs.itemconfig(peer.graph, fill=peer.bg)

        if recur_time > 0:

            self.time_elapsed += recur_time

            self.weight = min(self.weight + 0.01, 1)

            if self.weight < 1:

                self.parent.after(recur_time, lambda: self.update_font_colours(recur_time = self.recur_time))

        return

    def get_weight(self):
        return self.weight



class popup_window:
    def __init__(self, master, title=""):
        self.top=Toplevel(master)
        self.top.title(title)
        # Text entry
        lbl = Label(self.top, text="Duration (mins): ")
        lbl.grid(row=0, column=0, sticky=W)
        self.text=Entry(self.top)
        self.text.grid(row=0, column=1, sticky=NSEW)
        self.value = None
        # Ok button
        self.button=Button(self.top,text='Ok',command=self.cleanup)
        self.button.grid(row=1, column=0, columnspan=2, sticky=NSEW)
        # Enter shortcut
        self.top.bind("<Return>", self.cleanup)
        # Start
        self.center()

    def cleanup(self, event=None):
        """ Stores the data in the entry fields then closes the window """
        self.value = float(self.text.get())
        self.top.destroy()

    def center(self):
        """ Centers the popup in the middle of the screen """
        self.top.update_idletasks()
        w = self.top.winfo_screenwidth()
        h = self.top.winfo_screenheight()
        size = tuple(int(_) for _ in self.top.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        self.top.geometry("%dx%d+%d+%d" % (size + (x, y)))
        return