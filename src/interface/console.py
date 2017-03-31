from  Tkinter import *
import Queue

class Console(Text):
    def __init__(self, root, **kwargs):
        # Inherit
        Text.__init__(self, root, **kwargs)       

        # Queue waits for messages to be added to the console
        self.queue = Queue.Queue()
        
        self.bind("<Key>", self.null)

        self.update_me()

    def null(self, event):
        return "break"

    def update_me(self):
        try:
            while True:
                string = self.queue.get_nowait()
                self.insert(END, string + "\n")
                self.see(END)
                self.update_idletasks()
        except Queue.Empty:
            pass
        self.after(100, self.update_me)

    def write(self, string):
        if string != "\n":
            self.queue.put(string)
        return
        
