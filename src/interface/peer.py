from __future__ import absolute_import

try:
    import Tkinter as Tk
except ImportError:
    import tkinter as Tk
    
from ..config import *
import colorsys

def rgb2hex(*rgb): 
    r = int(max(0, min(rgb[0], 255)))
    g = int(max(0, min(rgb[1], 255)))
    b = int(max(0, min(rgb[2], 255)))
    return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

def hex2rgb(value):
    value = value.lstrip('#')
    return tuple(int(value[i:i+2], 16) for i in range(0,6,2) )

def avg_colour(col1, col2, weight=0.5):
    rgb1 = hex2rgb(col1)
    rgb2 = hex2rgb(col2)
    avg_rgb = tuple(rgb1[i] * (1-weight) + rgb2[i] * weight for i in range(3))
    return rgb2hex(*avg_rgb)

def int2rgb(i):
    h = (((i + 2) * 70) % 255) / 255.0
    return [int(n * 255) for n in colorsys.hsv_to_rgb(h, 1, 1)]

def PeerFormatting(index):
    i = index % len(COLOURS["Peers"])
    c = COLOURS["Peers"][i]
    return c, "Black"

class PeerColourTest:
    def __init__(self):
        self.root=Tk.Tk()
        num = 20
        h = 30
        w = 100
        self.canvas =Tk.Canvas(self.root, width=300, height=num*h)
        self.canvas.pack()
        m = 0
        for n in range(num):
            rgb = int2rgb(n)
            m = 0
            self.canvas.create_rectangle(m * w, n * h, (m + 1) * w,  (n + 1) * h, fill=rgb2hex(*rgb))
            m = 1
            rgb = tuple(n - 30 for n in rgb)
            self.canvas.create_rectangle(m * w, n * h, (m + 1) * w,  (n + 1) * h, fill=rgb2hex(*rgb))
            m = 2
            self.canvas.create_rectangle(m * w, n * h, (m + 1) * w,  (n + 1) * h, fill="Black")
        self.root.mainloop()



class Peer:
    """ Class representing the connected performers within the Tk Widget
    """
    def __init__(self, id_num, name, widget, row=1, col=0):
        self.id = id_num
        self.root = widget # Text
        self.root_parent = widget.root

        self.name = Tk.StringVar()
        self.name.set(name)

        self.update_colours()
        
        self.label = Tk.Label(self.root,
                           textvariable=self.name,
                           bg=self.bg,
                           fg=self.fg,
                           font="Font")

        self.insert = Tk.Label(self.root,
                            bg=self.bg,
                            fg=self.fg,
                            bd=0,
                            height=2,
                            text="", font="Font" )

        self.text_tag = "text_" + str(self.id)
        self.code_tag = "code_" + str(self.id)
        self.sel_tag  = "sel_"  + str(self.id)
        self.str_tag  = "str_"  + str(self.id) 
        self.mark     = "mark_" + str(self.id)

        self.root.peer_tags.append(self.text_tag)

        # Stat graph

        self.count = 0
        self.graph = None

        self.configure_tags()
        
        # Tracks a peer's selection amount and location
        self.row = row
        self.col = col
        self.index_num = 0
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        # self.move(1,0) # create the peer

    def __str__(self):
        return str(self.name.get())

    def get_peer_formatting(self, index):

        fg, bg = PeerFormatting(index)

        if self.root.merge_colour is not None:
            
            w = self.root.get_peer_colour_merge_weight()

            fg = avg_colour(fg, self.root.merge_colour, w)

        return fg, bg

    def update_colours(self):
        self.bg, self.fg = self.get_peer_formatting(self.id)
        return self.bg, self.fg

    def configure_tags(self):
        doing = True
        while doing:
            try:
                # Text tags
                self.root.tag_config(self.text_tag, foreground=self.bg)
                self.root.tag_config(self.str_tag,  foreground=self.fg)
                self.root.tag_config(self.code_tag, background=self.bg, foreground=self.fg)
                self.root.tag_config(self.sel_tag,  background=self.bg, foreground=self.fg)
                # Label
                self.label.config(bg=self.bg, fg=self.fg)
                self.insert.config(bg=self.bg, fg=self.fg)
                doing = False
            except TclError:
                pass
        return

    def shift(self, amount):
        return self.move(self.index_num + amount)
        
    def move(self, loc, raised = False):
        """ Updates the location of the Peer's label """

        try:

            document_length = len(self.root.read())

            # Make sure the location is valid

            if loc < 0:

                self.index_num = 0

            elif loc > document_length:

                self.index_num = document_length

            else:

                self.index_num = loc

            # Work with tcl indexing e.g. "1.0"
            
            index = self.root.number_index_to_tcl(loc)

            row, col = [int(val) for val in index.split(".")]

            if index == self.root.index(Tk.END):

                self.row = row - 1
                end_index = self.root.index(str(self.row) + ".end")

                self.col = int(end_index.split(".")[1])

            else:

                self.row = row
                self.col = col

            index = "{}.{}".format(self.row, self.col)

            # Find out if this needs to be raised

            # // TODO

            # Update the Tk text tag

            self.root.mark_set(self.mark, index)

            # Only move the cursor if we have a valid index

            bbox = self.root.bbox(index)

            if bbox is not None:

                x, y, width, height = bbox

                x_val = x - 2

                # Label can go on top of the cursor

                if raised:

                    y_val = (y - height, y - height)

                else:

                    y_val = (y + height, y)
                
                self.label.place(x=x_val, y=y_val[0], anchor="nw")
                self.insert.place(x=x_val, y=y_val[1], anchor="nw")

            else:

                # If we're not meant to see the peer, hide it
                
                self.label.place(x=-100, y=-100)
                self.insert.place(x=-100, y=-100)

        except Tk.TclError as e:

            print(e)
            
        return self.index_num

    def select(self, start, end):
        """ Highlights text selected by this peer"""
        self.root.tag_remove(self.sel_tag, "1.0", Tk.END)
        start, end = self.root.sort_indices([start, end])
        self.sel_start = start
        self.sel_end   = end  
        if start != end:
            self.root.tag_add(self.sel_tag, self.sel_start, self.sel_end)
        return

    def remove(self):
        self.label.destroy()
        self.insert.destroy()
        self.root.root.graphs.delete(self.graph)
        del self.root.peers[self.id]
        return self
    
    def hasSelection(self):
        return self.sel_start != self.sel_end != "0.0"
    
    def deleteSelection(self):
        self.root.tag_remove(self.sel_tag, self.sel_start, self.sel_end)
        self.root.delete(self.sel_start, self.sel_end)
        row, col = self.sel_start.split(".")
        self.move(row, col)
        self.sel_start = "0.0"
        self.sel_end   = "0.0"
        return

    def highlight(self, start_line, end_line):
        """ Highlights (and schedules de-highlight) of block of text. Returns contents
            as a string """

        code = []

        if start_line == end_line: 
            end_line += 1

        for line in range(start_line, end_line):
            
            start = "%d.0" % line
            end   = "%d.end" % line

            # Highlight text only to last character, not whole line

            self.__highlight_block(start, end)

            code.append(self.root.get(start, end))
            
        # Unhighlight the line of text

        self.root.master.after(200, self.__unhighlight_block)

        return "\n".join(code)

    def __highlight_block(self, start, end):
        self.root.tag_add(self.code_tag, start, end)
        return

    def __unhighlight_block(self):
        self.root.tag_remove(self.code_tag, "1.0", Tk.END)
        return

    def get_tcl_index(self):
        """ Returns the index number as a Tkinter index e.g. "1.0" """
        return self.root.number_index_to_tcl(self.index_num)

    def get_index_num(self):
        """ Returns the index (a single integer) of this peer, if it isn't valid, it 
            will adjust the peer """
        return self.index_num
    
    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id
