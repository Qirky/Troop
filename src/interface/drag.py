try:
    from Tkinter import Frame
except ImportError:
    from tkinter import Frame

class Dragbar(Frame):

    def __init__(self, master, *args, **kwargs):

        self.app  = master
        self.root = master.root

        Frame.__init__( self,
                        self.root ,
                        bg="white",
                        height=2,
                        cursor="sb_v_double_arrow")

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

            textbox_line_h = self.app.text.dlineinfo("@0,0")

            if textbox_line_h is not None:

                line_height = textbox_line_h[3]

                text_height = int( self.app.text.winfo_height() / line_height ) # In lines

                widget_y = self.app.console.winfo_rooty() # Location of the console

                new_height =  ( self.app.console.winfo_height() + (widget_y - event.y_root) )

                # Update heights of console / graphs

                self.app.graphs.config(height = new_height)

                self.app.console.config(height = max(2, new_height / line_height))

            return "break"
