try:
    import Tkinter as Tk
    import tkMessageBox
    import tkFileDialog
except ImportError:
    import tkinter as Tk
    from tkinter import messagebox as tkMessageBox
    from tkinter import filedialog as tkFileDialog

from .interface import ROOT
from ..config import langtitles

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
            self.root.resizable(False, False)
            
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
            self.name.grid(row=2, column=1, sticky=Tk.NSEW)
            
            # Password
            lbl = Tk.Label(self.root, text="Password: ")
            lbl.grid(row=3, column=0, sticky=Tk.W)
            self.password=Tk.Entry(self.root, show="*")
            self.password.grid(row=3, column=1, sticky=Tk.NSEW)

            # Interpreter
            lbl = Tk.Label(self.root, text="Language: ")
            lbl.grid(row=4, column=0, sticky=Tk.W)
            self.select_path_option = "Select another program..."
            options = list(langtitles.values()) + [self.select_path_option]
            self.lang = Tk.StringVar(self.root)
            self.lang.set(langtitles.get(kwargs.get('lang', 'foxdot').lower(), 'FoxDot'))
            self.drop = Tk.OptionMenu(self.root, self.lang, *list(options), command=self.select_path)
            self.drop.config(width=5)
            self.drop.grid(row=4, column=1, sticky=Tk.NSEW)

            # Invisible syntax highlighting option
            self.syntax_label = Tk.Label(self.root, text="Syntax: ")
            options = list(langtitles.values())
            self.syntax = Tk.StringVar(self.root)
            self.syntax.set(langtitles.get(kwargs.get('syntax', 'foxdot').lower(), 'FoxDot'))
            self.syntax_drop = Tk.OptionMenu(self.root, self.syntax, *options)
            self.syntax_drop.config(width=5)

            if "syntax" in self.options:
                self.show_syntax_options()
            else:
                self.hide_syntax_options() 

            # Ok button
            self.button=Tk.Button(self.root, text='Ok',command=self.store_data)
            self.button.grid(row=6, column=0, columnspan=2, sticky=Tk.NSEW)

            self.response = Tk.StringVar()
            self.lbl_response=Tk.Label(self.root, textvariable=self.response, fg="Red")
            self.lbl_response.grid(row=7, column=0, columnspan=2)
            self.lbl_response.grid_remove()
            
            # Value
            self.data = {}
            
            # Enter shortcut
            self.root.bind("<Return>", self.store_data)

    def start(self):
        if self.using_gui_input:
            self.center()
            self.mainloop() # calls finish from the OK button
        else:
            self.finish()

    def mainloop(self):        
        if self.client.mainloop_started is False:
            try:
                self.client.mainloop_started = True
                self.root.mainloop()
            except KeyboardInterrupt:
                self.client.kill()
        return

    def quit(self):
        self.data = {}
        return self.root.quit()

    def finish(self):
        """ Starts the client connection"""
        self.client.setup(**self.options)
        return

    def cleanup(self):
        """ Removes all the widgets from the root """
        if self.using_gui_input:
            for widget in self.root.winfo_children():
                widget.grid_forget()
        return

    def select_path(self, lang):
        """ If lang is select_path_option, open file dialog and set self.lang to the path """
        if lang == self.select_path_option:
            path = tkFileDialog.askopenfilename(initialdir = "/",title = "Select file")
            self.lang.set(path)
        elif lang == langtitles["none"]:
            self.show_syntax_options()
        else:
            self.hide_syntax_options()
        return

    def show_syntax_options(self):
        """ Use 'grid' to show options for selecting syntax highlighting """
        self.syntax_drop.grid(row=5, column=1, sticky=Tk.NSEW)
        self.syntax_label.grid(row=5, column=0, sticky=Tk.W)
        return

    def hide_syntax_options(self):
        """ Use 'grid_forget' to hide syntax options """
        self.syntax_drop.grid_forget()
        self.syntax_label.grid_forget()
        return

    def select_syntax(self, lang):
        """ Store the name of the interpreter syntax highlighting to use """
        return

    def store_data(self, event=None):
        """ Stores the data in the entry fields then closes the window """
        host = self.host.get()
        port = self.port.get()
        name = self.name.get()
        password = self.password.get()

        # Use correct formatting of lang_name and syntax_name
        
        lang_name = self.lang.get()
        syntax_name = self.syntax.get()

        for short_name, long_name in langtitles.items():

            if long_name == lang_name:

                lang_name = short_name

            if long_name == syntax_name:

                syntax_name = short_name

        # If we have values for name, host, and port then go to "finish"

        if name.strip() != "" and host.strip() != "" and port.strip() != "":

            self.options.update(  
                host = host, 
                port = port, 
                name = name, 
                password = password,
                lang = lang_name,
                syntax = syntax_name
            )

            self.finish()

        return

    def center(self):
        """ Centers the popup in the middle of the screen """
        self.root.update_idletasks()
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        size = tuple(int(_) for _ in self.root.geometry().split('+')[0].split('x'))
        x = int(w/2 - size[0]/2)
        y = int(h/2 - size[1]/2)
        self.root.geometry("+{}+{}".format(x, y))
        self.lbl_response.config(wraplength=size[0])
        self.name.focus()
        return        

    def print_message(self, message):
        """ Displays the response message to the user """
        if self.using_gui_input:
            self.response.set(message)
            self.lbl_response.grid()
        else:
            print(message)
        return
