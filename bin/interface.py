from Tkinter import *
import tkFont

class Interface:
    def __init__(self, title="Troop"):
        self.root=Tk()
        self.root.title(title)
        self.root.protocol("WM_DELETE_WINDOW", self.kill )
        # Scroll bar
        self.scroll = Scrollbar(self.root)
        self.scroll.grid(row=0, column=1, sticky='nsew')
        # Text box
        self.text=ThreadSafeText(self.root)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.scroll.config(command=self.text.yview)
        self.text.focus_set()
        # Key bindings
        self.text.bind("<Key>",             self.KeyPress)
        self.text.bind("<Control-Return>",  self.Execute)
        self.text.bind("<<Selection>>",     self.Selection)
        # Selection indices
        self.sel_start = "0.0"
        self.sel_end   = "0.0"
        # Listener
        self.pull = lambda *x: None
        # Sender
        self.push = lambda *x: None
        
    def run(self):
        self.root.mainloop()
        
    def kill(self):
        try: self.pull.quit()
        except: pass
        self.root.destroy()

    @staticmethod
    def convert(index):
        return (int(value) for value in index.split("."))

    def setMarker(self, id_num, name):
        self.text.marker=Peer(id_num, self.text)
        self.text.marker.name.set(name)
        
    def write(self, msg):
        """ Writes a network message to the queue
        """
        # Keep information about new peers
        sender_id = int(msg[0])
        if sender_id not in self.text.peers:
            self.text.peers[sender_id] = Peer(sender_id, self.text)
            self.text.peers[sender_id].name.set(self.pull(sender_id, "name"))
        # Add message to queue
        self.text.queue.put(msg)
        return
    
    def KeyPress(self, event):
        """ 'Pushes' the key-press to the server.
            - Character
            - Line and column number
            - Timestamp
        """
        row, col = self.text.index(INSERT).split(".")
        row = int(row)
        col = int(col)

        ret = None # Set to "break" if need be

        if event.keysym == "Delete":
            char = "del"
        elif event.keysym == "BackSpace":
            char = "bsp"
        elif event.keysym == "Return":
            char = "\n"
        elif event.keysym == "Tab":
            char = "    "
            col += len(char)
            ret  = "break"
            self.text.insert(INSERT, char)
        else:
            char = event.char

        self.push(char, row, col, event.time)

        # Update the local client's label
        if self.text.marker is not None:
            self.text.marker.move(row, col)
            
        return ret

    def Selection(self, event):
        """ """
        try:
            self.sel_start = self.text.index(SEL_FIRST)
            self.sel_end   = self.text.index(SEL_LAST)
        except:
            self.sel_start = "0.0"
            self.sel_end   = "0.0"
        print self.sel_start, self.sel_end
        self.push("sel", self.sel_start, self.sel_end)
        return

    def Execute(self, event):
        return "break"


import Queue
class ThreadSafeText(Text):
    def __init__(self, master, **options):
        Text.__init__(self, master, **options)
        self.queue = Queue.Queue()

        # Markers for users, including the current one
        self.marker = None
        self.peers = {}

        # Font
        self.font = tkFont.Font(font=("Consolas", 12), name="Font")
        self.font.configure(**tkFont.nametofont("Font").configure())
        self.configure(font="Font")
        
        self.update_me()
    
    def update_me(self):
        try:
            while True:

                msg = self.queue.get_nowait()

                # Get message contents
                ID   = int(msg[0])
                char = str(msg[1])

                this_peer = self.peers[ID]

                # Handles selection changes

                if char == "sel":

                    sel1 = str(msg[2])
                    sel2 = str(msg[3])
                    
                    this_peer.select(sel1, sel2)

                # Handles keypresses

                else:
                    
                    line = int(msg[2])
                    col  = int(msg[3])

                    # Delete
                    
                    if char == "del":

                        if this_peer.hasSelection():

                            this_peer.deleteSelection()

                        else:

                            index = "{}.{}".format(line, col)

                            self.delete(index)

                    # Backspace

                    elif char == "bsp":

                        if this_peer.hasSelection():

                            this_peer.deleteSelection()

                        else:

                            # Move the cursor left one for a backspace

                            index = "{}.{}".format(line, col-1)

                            if line > 0 and col > 0:

                                self.delete(index)

                    # Other
                    
                    else:

                        index = "{}.{}".format(line, col)

                        if len(char) > 0 and this_peer.hasSelection():

                            this_peer.deleteSelection()

                        self.insert(index, char)

                    # Update the peer's marker

                    this_peer.move(line, col)

                # Update any other idle tasks

                self.update_idletasks()

        # Break when the queue is empty
        except Queue.Empty:
            pass

        # Recursive call
        self.after(100, self.update_me)
        return

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

        self.tag_name = "tag_" + str(self.id)
        self.root.tag_config(self.tag_name, background=self.bg)

        # Tracks a peer's selection amount
        self.sel_start = "0.0"
        self.sel_end   = "0.0"

        self.name.set("Unnamed Peer")
        self.move(1,0)
        
    def move(self, row, col):
        """ Updates information about this Peer from a network message """
        x = self.root.font.measure(" " * col)
        y = self.root.font.metrics("linespace") * row
        self.label.place(x=x, y=y)
        return

    def select(self, start, end):
        """ Highlights text selected by this peer"""
        if start != end != "0.0":
            self.sel_start = start
            self.sel_end   = end
            self.root.tag_add(self.tag_name, self.sel_start, self.sel_end)
        else:
            self.root.tag_remove(self.tag_name, self.sel_start, self.sel_end)
            self.sel_start = start
            self.sel_end   = end            
        return
    
    def hasSelection(self):
        return self.sel_start != self.sel_end != "0.0"
    
    def deleteSelection(self):
        self.root.tag_remove(self.tag_name, self.sel_start, self.sel_end)
        self.root.delete(self.sel_start, self.sel_end)
        self.sel_start = "0.0"
        self.sel_end   = "0.0"
        return
    
    def __eq__(self, other):
        return self.id == other
    def __ne__(self, other):
        return self.id != other


if __name__ == "__main__":
    # Testing
    i = Interface()
    i.run()
