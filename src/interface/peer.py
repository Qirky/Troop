from Tkinter import *

PeerColours = [
    ("green",   "black"),
    ("cyan",    "black"),
    ("yellow",  "black"),
    ("magenta", "white"),
    ("white",   "black"),
    ("red",     "white"),
    ("blue",    "white")
]


class Peer:
    """ Class representing the connected performers within the Tk Widget
    """
    def __init__(self, id_num, widget):
        self.id = id_num
        self.root = widget

        self.name = StringVar()
        
        self.bg = PeerColours[self.id % len(PeerColours)][0]
        self.fg = PeerColours[self.id % len(PeerColours)][1]
        
        self.label = Label(self.root,
                           textvariable=self.name,
                           bg=self.bg,
                           fg=self.fg,
                           font="Font")

        self.insert = Label(self.root,
                            bg=self.bg,
                            fg=self.fg,
                            text="" )

        self.text_tag = "text_" + str(self.id)
        self.code_tag = "code_" + str(self.id)
        self.sel_tag  = "sel_"  + str(self.id)
        self.mark     = "mark_" + str(self.id)

        self.root.mark_set(self.mark, "0.0")
        self.root.peer_tags.append(self.text_tag)

        # Stat graph
        self.count = 0
        self.graph = self.root.root.graphs.create_rectangle(0,0,0,0, fill=self.bg)

        # Tracks a peer's selection amount and location
        self.row = 1
        self.col = 0
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        self.root.tag_config(self.text_tag, foreground=self.bg)
        self.root.tag_config(self.code_tag, background=self.bg, foreground=self.fg)
        self.root.tag_config(self.sel_tag, background=self.bg, foreground=self.fg)

        self.char_w = self.root.font.measure(" ")
        self.char_h = self.root.font.metrics("linespace")

        self.name.set("Unnamed Peer")
        self.move(self.row, self.col)

    def __str__(self):
        return str(self.name.get())
        
    def move(self, row, col):
        """ Updates information about this Peer from a network message.
            TODO - Add an insert cursor for each peer """

        index = "{}.{}".format(row, col)

        if index == self.root.index(END):

            self.row = row - 1
            end_index = self.root.index(str(self.row) + ".end")

            self.col = int(end_index.split(".")[1])

        else:

            self.row = row
            self.col = col

        index = "{}.{}".format(self.row, self.col)

        x = (self.root.char_w * (self.col + 1)) % self.root.winfo_width()
        y = self.root.dlineinfo(index)

        # Only move the cursor if we have a valid index
        if y is not None:
            
            self.label.place(x=x, y=y[1]+self.root.char_h, anchor="nw")
            
        return

    def select(self, start, end):
        """ Highlights text selected by this peer"""
        self.root.tag_remove(self.sel_tag, "1.0", END)
        self.sel_start = start
        self.sel_end   = end  
        if start != end: # != "0.0":
            self.root.tag_add(self.sel_tag, self.sel_start, self.sel_end)                      
        return

    def remove(self):
        self.label.destroy()
        self.root.root.graphs.delete(self.graph)
        return
    
    def hasSelection(self):
        return self.sel_start != self.sel_end != "0.0"
    
    def deleteSelection(self):
        self.root.tag_remove(self.sel_tag, self.sel_start, self.sel_end)
        self.root.delete(self.sel_start, self.sel_end)
        self.sel_start = "0.0"
        self.sel_end   = "0.0"
        return

    def highlightBlock(self, lines):

        a, b = (int(x) for x in lines)

        if a == b: b += 1

        for line in range(a, b):
            start = "%d.0" % line
            end   = "%d.end" % line

            # Highlight text only to last character, not whole line

            self.highlight(start, end)
            
        # Unhighlight the line of text

        self.root.master.after(200, self.unhighlight)

        return

    def highlight(self, start, end):
        self.root.tag_add(self.code_tag, start, end)
        return

    def unhighlight(self):
        self.root.tag_remove(self.code_tag, "1.0", END)
        return
    
    def __eq__(self, other):
        return self.id == other
    def __ne__(self, other):
        return self.id != other
