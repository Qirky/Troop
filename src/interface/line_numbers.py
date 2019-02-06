from __future__ import absolute_import
try:
    import Tkinter as Tk
except:
    import tkinter as Tk

from ..config import *

class LineNumbers(Tk.Canvas):
    def __init__(self, master, *args, **kwargs):
        Tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = master
        self.redraw()

    def redraw(self, *args):
        '''Redraws the line numbers at 30 fps'''
        self.delete("all")

        i = self.textwidget.index("@0,0")

        self.config(width=self.textwidget.font.measure(str(max(self.textwidget.get_num_lines(), 10))) + 20)

        w = self.winfo_width() - 5 # Width

        while True:

            dline=self.textwidget.dlineinfo(i)

            if dline is None:
                break

            y = dline[1]
            h = dline[3]

            linenum = int(str(i).split(".")[0])

            # If the linenum is the currently edited linenumber, highlight

            if self.textwidget.marker is not None:

                if linenum == self.textwidget.marker.row:

                    x1, y1 = 0, y
                    x2, y2 = w, y + h

                    self.create_rectangle(x1, y1, x2, y2, fill="gray30", outline="gray30")

            self.create_text(w - 4, y, anchor="ne",
                             justify=Tk.RIGHT,
                             text=linenum,
                             font="Font",
                             fill="#d3d3d3")


            i = self.textwidget.index("{}+1line".format(i))

        # Draw a line

        self.create_line(w, 0, w, self.winfo_height(), fill="gray50")

        # Draw peer_lables

        if self.textwidget.is_refreshing is False:

            self.textwidget.refresh_peer_labels()

        self.after(30, self.redraw)
