from Tkinter import *

PeerColours = {"red"    : "white",
               "green"  : "white",
               "blue"   : "white",
               "yellow" : "black",
               "purple" : "white" }


class Peer:
    """ Class representing the connected performers within the Tk Widget
    """
    def __init__(self, id_num, widget):
        self.id = id_num
        self.root = widget

        self.name = StringVar()
        
        self.bg = sorted(PeerColours.keys())[self.id]
        self.fg = PeerColours[self.bg]
        
        self.label = Label(self.root,
                           textvariable=self.name,
                           bg=self.bg,
                           fg=self.fg,
                           font="Font")

        self.insert = Label(self.root,
                            bg=self.bg,
                            fg=self.fg,
                            text="" )

        self.tag_name = "tag_" + str(self.id)
        self.mark     = "mark_" + str(self.id)
        self.root.mark_set(self.mark, "0.0")

        # Tracks a peer's selection amount
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        self.root.tag_config(self.tag_name, background=self.bg)

        self.char_w = self.root.font.measure(" ")
        self.char_h = self.root.font.metrics("linespace")

        self.name.set("Unnamed Peer")
        self.move(1,0)

    def __str__(self):
        return str(self.name.get())
        
    def move(self, row, col):
        """ Updates information about this Peer from a network message.
            TODO - Add an insert cursor for each peer """

        x = (self.char_w * (col + 1)) % self.root.winfo_width()
        y = self.root.dlineinfo("{}.{}".format(row, col))

        # Only move the cursor if we have a valid index
        if y is not None:
            self.label.place(x=x, y=y[1]+self.char_h)
            
        return

    def select(self, start, end):
        """ Highlights text selected by this peer"""
        self.root.tag_remove(self.tag_name, "1.0", END)
        self.sel_start = start
        self.sel_end   = end  
        if start != end: # != "0.0":
            self.root.tag_add(self.tag_name, self.sel_start, self.sel_end)                      
        return

    def remove(self):
        self.label.destroy()
        return
    
    def hasSelection(self):
        return self.sel_start != self.sel_end != "0.0"
    
    def deleteSelection(self):
        self.root.tag_remove(self.tag_name, self.sel_start, self.sel_end)
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
        self.root.tag_add("code", start, end)
        self.root.tag_config("code", background=self.bg, foreground=self.fg)
        
        return

    def unhighlight(self):
        self.root.tag_delete("code")
        return
    
    def __eq__(self, other):
        return self.id == other
    def __ne__(self, other):
        return self.id != other
