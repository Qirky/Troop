from  Tkinter import *
import Queue

class Console(Text):
    def __init__(self, root, **kwargs):
        Text.__init__(self, root, **kwargs)
        self.queue = Queue.Queue()
        self.bind("<Key>", lambda e: "break")
        self.update_me()

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
        
