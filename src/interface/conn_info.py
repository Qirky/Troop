try:
    import Tkinter as Tk
except ImportError:
    import tkinter as Tk

from .interface import ROOT

class ConnectionInput:
    """ Interface for getting connection info from the user """
    def __init__(self, client, get_info=True, **kwargs):

        self.client  = client
        self.using_gui_input = get_info
        self.options = kwargs
        self.root=ROOT

        # If there is all the info, go straight to main interface

        if self.using_gui_input:

            self.root.title("Troop v{}".format(client.version))
            self.root.protocol("WM_DELETE_WINDOW", self.quit )
            
            # Host
            lbl = Tk.Label(self.root, text="Host:")
            lbl.grid(row=0, column=0, stick=Tk.W)
            self.host=Tk.Entry(self.root)
            self.host.insert(0, kwargs.get("host", "localhost"))
            self.host.grid(row=0, column=1, sticky=Tk.NSEW)

            # Port
            lbl = Tk.Label(self.root, text="Port:")
            lbl.grid(row=1, column=0, stick=Tk.W)
            self.port=Tk.Entry(self.root)
            self.port.insert(0, kwargs.get("port", "57890"))
            self.port.grid(row=1, column=1, sticky=Tk.NSEW)
            
            # Name
            lbl = Tk.Label(self.root, text="Name:")
            lbl.grid(row=2, column=0, sticky=Tk.W)
            self.name=Tk.Entry(self.root)
            self.name.grid(row=2, column=1)
            
            # Password
            lbl = Tk.Label(self.root, text="Password: ")
            lbl.grid(row=3, column=0, sticky=Tk.W)
            self.password=Tk.Entry(self.root, show="*")
            self.password.grid(row=3, column=1)
            
            # Ok button
            self.button=Tk.Button(self.root, text='Ok',command=self.cleanup)
            self.button.grid(row=4, column=0, columnspan=2, sticky=Tk.NSEW)
            
            # Value
            self.value = None
            
            # Enter shortcut
            self.root.bind("<Return>", self.cleanup)

            self.start()  # run

        else:

            self.finish() # skip getting info if we have it already

    def start(self):
        # Start
        self.center()
        self.mainloop()


    def mainloop(self):        
        try:
            self.client.mainloop_started = True
            self.root.mainloop()
        except KeyboardInterrupt:
            self.client.kill()
        return

    def quit(self):
        self.value = None
        return self.root.quit()

    def finish(self):
        """ Removes the widgetes from the Tk instance and starts the client connection"""
        for widget in self.root.winfo_children():
            widget.grid_forget()
        self.client.setup(**self.options)
        return

    def cleanup(self, event=None):
        """ Stores the data in the entry fields then closes the window """
        host = self.host.get()
        port = self.port.get()
        name = self.name.get()
        password = self.password.get()

        if name.strip() != "" and host.strip() != "" and port.strip() != "":

            self.options.update(  
                host = host, 
                port = port, 
                name = name, 
                password = password
            )

            self.finish()

        return

    def center(self):
        """ Centers the popup in the middle of the screen """
        self.root.update_idletasks()
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        size = tuple(int(_) for _ in self.root.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        self.root.geometry("%dx%d+%d+%d" % (size + (x, y)))
        self.name.focus()
        return        

    def get_info(self):
        return self.value

    def exit(self, message):
        """ Exits the interface with an input box but using sys.exit if -i flag was given """
        if self.using_gui_input:
            pass # bell
        else:
            sys.exit(message)