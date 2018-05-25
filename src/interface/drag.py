try:
    from Tkinter import Frame
except ImportError:
    from tkinter import Frame

class Dragbar(Frame):
    cursor_style="sb_v_double_arrow"
    def __init__(self, master, *args, **kwargs):

        self.app  = master
        self.root = master.root

        kwargs["cursor"]=self.cursor_style

        Frame.__init__( self, self.root, **kwargs )

        self.mouse_down = False
        
        self.bind("<Button-1>",        self.drag_mouseclick)        
        self.bind("<ButtonRelease-1>", self.drag_mouserelease)
        self.bind("<B1-Motion>",       self.drag_mousedrag)

    def drag_mouseclick(self, event):
        """ Allows the user to resize the console height """
        self.mouse_down = True
        self.root.grid_propagate(False)
        return
    
    def drag_mouserelease(self, event):
        self.mouse_down = False
        self.app.text.focus_set()
        return

    def drag_mousedrag(self, event):
        if self.mouse_down:

            line_height = self.app.text.char_h

            text_height = ( self.app.text.winfo_height() / line_height ) # In lines

            widget_y = self.app.console.winfo_rooty() # Location of the console

            new_height =  ( self.app.console.winfo_height() + (widget_y - event.y_root) )

            # Update heights of console / graphs

            self.app.graphs.config(height = int(new_height))

            self.app.console.config(height = int(max(2, new_height / line_height)))

        return "break"

class ConsoleDragbar(Dragbar):
    cursor_style="sb_h_double_arrow"
    def drag_mousedrag(self, event):
        """ Resize the canvas """
        if self.mouse_down:

            widget_x = self.app.graphs.winfo_rootx() # Location of the graphs

            new_width =  self.app.graphs.winfo_width() + (widget_x - event.x_root)

            self.app.graphs.config(width = int(new_width))

            console_width = (self.app.root.winfo_width() - new_width) / self.app.text.char_w
            
            self.app.console.config(width = int(console_width))

        return "break"
