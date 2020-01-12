"""
    Interpreter
    -----------

    Runs a block of FoxDot code. Designed to be overloaded
    for other language communication

"""
from __future__ import absolute_import
from .config import *
from .message import MSG_CONSOLE

from subprocess import Popen
from subprocess import PIPE, STDOUT
from datetime import datetime

# Import OSC library depending on Python version

if PY_VERSION == 2:
    from . import OSC
else:
    from . import OSC3 as OSC

try:
    broken_pipe_exception = BrokenPipeError
except NameError:  # Python 2
    broken_pipe_exception = IOError

CREATE_NO_WINDOW = 0x08000000 if SYSTEM == WINDOWS else 0

import sys
import re
import time
import threading
import shlex
import tempfile
import os, os.path

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

def compile_regex(kw):
    """ Takes a list of strings and returns a regex that
        matches each one """
    return re.compile(r"(?<![a-zA-Z.])(" + "|".join(kw) + ")(?![a-zA-Z])")

SEPARATOR = ":"; _ = " %s " % SEPARATOR

def colour_format(text, colour):
    return '<colour="{}">{}</colour>'.format(colour, text)

## dummy interpreter

class DummyInterpreter:
    name = None
    def __init__(self, *args, **kwargs):
        self.re={}
        
        self.syntax_lang = langtypes[kwargs.get("syntax", -1)]

        # If using another snytax, use the appropriate regex

        if self.syntax_lang != self.__class__:
        
            self.re = {"tag_bold": self.syntax_lang.find_keyword, "tag_italic": self.syntax_lang.find_comment}

            self.syntax_lang.setup()

        else:

            self.syntax_lang = None

    def __repr__(self):
        return self.name if name is not None else repr(self.__class__.__name__)

    def get_block_of_code(self, text, index):
        """ Returns the start and end line numbers of the text to evaluate when pressing Ctrl+Return. """

        # Get start and end of the buffer
        start, end = "1.0", text.index("end")
        lastline   = int(end.split('.')[0]) + 1

        # Indicies of block to execute
        block = [0,0]        
        
        # 1. Get position of cursor
        cur_x, cur_y = index.split(".")
        cur_x, cur_y = int(cur_x), int(cur_y)
        
        # 2. Go through line by line (back) and see what it's value is
        
        for line in range(cur_x, 0, -1):
            if not text.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[0] = line

        # 3. Iterate forwards until we get two \n\n or index==END
        for line in range(cur_x, lastline):
            if not text.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[1] = line

        return block
    
    def evaluate(self, string, *args, **kwargs):
        self.print_stdin(string, *args, **kwargs)
        return

    def start(self):
        return self
    
    def stdout(self, *args, **kwargs):
        pass
    
    def kill(self, *args, **kwargs):
        pass
    
    def print_stdin(self, string, name=None, colour="White"):
        """ Handles the printing of the execute code to screen with coloured
            names and formatting """
        # Split on newlines
        string = [line.replace("\n", "") for line in string.split("\n") if len(line.strip()) > 0]
        if len(string) > 0 and name is not None:
            name = str(name)
            print(colour_format(name, colour) + _ + string[0])
            # Use ... for the remainder  of the  lines
            n = len(name)
            for i in range(1,len(string)):
                sys.stdout.write(colour_format("." * n, colour) + _ + string[i])
                sys.stdout.flush()
        return

    # Syntax highlighting methods

    def find_keyword(self, string):
        return self.syntax_lang.find_keyword(string)

    def find_comment(self, string):
        return self.syntax_lang.find_comment(string)

    def stop_sound(self):
        """ Returns the string for stopping all sound in a language """
        return self.syntax_lang.stop_sound() if self.syntax_lang != None else ""
    
    @staticmethod
    def format(string):
        """ Method to be overloaded in sub-classes for formatting strings to be evaluated """
        return str(string) + "\n"
    
class Interpreter(DummyInterpreter):
    id       = 99
    lang     = None
    clock    = None
    boot_file = None
    keyword_regex = compile_regex([])
    comment_regex = compile_regex([])
    stdout   = None
    stdout_thread = None
    filetype = ".txt"
    client   = None

    def __init__(self, client, path, args=""):

        self.client = client

        self.re = {"tag_bold": self.find_keyword, "tag_italic": self.find_comment}

        self.path = shlex.split(path)

        self.args = self._get_args(args)

        self.f_out = tempfile.TemporaryFile("w+", 1) # buffering = 1
        self.is_alive = True

        self.setup()

    @staticmethod
    def _get_args(args):
        if isinstance(args, str):
    
            args = shlex.split(args)

        elif isinstance(args, list) and len(args) == 1:

            args = shlex.split(args[0])

        return args

    def setup(self):
        """ Overloaded in sub-classes """
        return

    def start(self):
        """ Opens the process with the interpreter language """

        try:
        
            self.lang = Popen(self.path + self.args, shell=False, universal_newlines=True, bufsize=1,
                              stdin=PIPE,
                              stdout=self.f_out,
                              stderr=self.f_out,
    						  creationflags=CREATE_NO_WINDOW)

            self.stdout_thread = threading.Thread(target=self.stdout)
            self.stdout_thread.start()

        except OSError:

            raise ExecutableNotFoundError(self.get_path_as_string())

        self.load_bootfile()

        return self

    def load_bootfile(self):
        """ 
        Loads the specified boot file. If it exists, it is defined
        in the class but can be overridden in conf/boot.txt.
        """

        self.boot_file = self.get_custom_bootfile()

        # Load data
        if self.boot_file is not None:

            with open(self.boot_file) as f:

                for line in f.split("\n"):

                    self.lang.stdin.write(line.rstrip() + "\n")
                    self.lang.stdin.flush()

        return

    def get_custom_bootfile(self):
        """
        Get the path of a specific custom bootfile or None if it
        does not exist.
        """

        # Check boot file for overload

        if self.name is not None and os.path.exists(BOOT_CONFIG_FILE):

            with open(BOOT_CONFIG_FILE) as f:

                for line in f.readlines():

                    if line.startswith(self.name):

                        data = line.split("=")

                        path = data[-1].strip()

                        if path not in ("''", '""'):

                            return path

        return None

    def get_path_as_string(self):
        """ Returns the executable input as a string """
        return " ".join(self.path)

    @classmethod
    def find_keyword(cls, string):
        return [(match.start(), match.end()) for match in cls.keyword_regex.finditer(string)]

    @classmethod
    def find_comment(cls, string):
        return [(match.start(), match.end()) for match in cls.comment_regex.finditer(string)]

    def write_stdout(self, string):
        if self.is_alive:
            self.lang.stdin.write(self.format(string))
            self.lang.stdin.flush()
        return

    def evaluate(self, string, *args, **kwargs):
        """ Sends a string to the stdin and prints the text to the console """
        # TODO -- get control of stdout
        # Print to console
        self.print_stdin(string, *args, **kwargs)
        # Pipe to the subprocess
        self.write_stdout(string)
        return

    def stdout(self, text=""):
        """ Continually reads the stdout from the self.lang process """

        while self.is_alive:
            if self.lang.poll():
                self.is_alive = False
                break
            try:
                # Check contents of file
                # TODO -- get control of f_out and stdout
                self.f_out.seek(0)
                
                message = []
                
                for stdout_line in iter(self.f_out.readline, ""):
                
                    line = stdout_line.rstrip()
                    sys.stdout.write(line)
                    message.append(line)
                
                # clear tmpfile
                self.f_out.truncate(0)

                # Send console contents to the server

                if len(message) > 0 and self.client.is_master():
                    
                    self.client.send(MSG_CONSOLE(self.client.id, "\n".join(message)))

                time.sleep(0.05)
            except ValueError as e:
                print(e)
                return
        return

    def kill(self):
        """ Stops communicating with the subprocess """
        # End process if not done so already
        self.is_alive = False
        if self.lang.poll() is None:
            self.lang.communicate()

class CustomInterpreter:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    def __call__(self):
        return Interpreter(*self.args, **self.kwargs)

class BuiltinInterpreter(Interpreter):
    def __init__(self, client, args):   
        Interpreter.__init__(self, client, self.path, args)

class FoxDotInterpreter(BuiltinInterpreter):
    filetype=".py"
    path = "{} -u -m FoxDot --pipe".format(PYTHON_EXECUTABLE)
    name = "FoxDot"

    @classmethod
    def setup(cls):
        cls.keywords = ["Clock", "Scale", "Root", "var", "linvar", '>>', 'print']
        cls.keyword_regex = compile_regex(cls.keywords)

    @staticmethod
    def format(string):
        return "{}\n\n".format(string)

    @classmethod
    def find_comment(cls, string):        
        instring, instring_char = False, ""
        for i, char in enumerate(string):
            if char in ('"', "'"):
                if instring:
                    if char == instring_char:
                        instring = False
                        instring_char = ""
                else:
                    instring = True
                    instring_char = char
            elif char == "#":
              if not instring:
                  return [(i, len(string))]
        return []

    def kill(self):
        self.evaluate(self.stop_sound())
        Interpreter.kill(self)
        return

    @classmethod
    def stop_sound(cls):
        return "Clock.clear()"

class TidalInterpreter(BuiltinInterpreter):
    path = 'ghci'
    filetype = ".tidal"
    name = "TidalCycles"
    
    def start(self):

        # Use ghc-pkg to find location of boot-tidal

        try:

            process = Popen(["ghc-pkg", "field", "tidal", "data-dir"], stdout=PIPE, universal_newlines=True)

            output = process.communicate()[0]

            data_dir = output.split("\n")[0].replace("data-dir:", "").strip()

            self.boot_file = os.path.join(data_dir, "BootTidal.hs")

        except FileNotFoundError:

            # Set to None - might be defined in bootup file

            self.boot_file = None

        Interpreter.start(self)
        
        return self

    def load_bootfile(self):
        """
        Overload for Tidal to use :script /path/to/file
        instead of loading each line of a boot file one by
        one
        """
        self.boot_file = (self.get_custom_bootfile() or self.boot_file)

        if self.boot_file:

            self.write_stdout(":script {}".format(self.boot_file))

        else:

            err = "Could not find BootTidal.hs! You can specify the path in your Troop boot config file: {}".format(BOOT_CONFIG_FILE)
            raise(FileNotFoundError(err))

        return

    @classmethod
    def setup(cls):
        cls.keywords  = ["d{}".format(n) for n in range(1,17)] + ["\$", "#", "hush", "solo", "silence"]
        cls.keyword_regex = compile_regex(cls.keywords)
        return

    @classmethod
    def find_comment(cls, string):        
        instring, instring_char = False, ""
        for i, char in enumerate(string):
            if char in ('"', "'"):
                if instring:
                    if char == instring_char:
                        instring = False
                        instring_char = ""
                else:
                    instring = True
                    instring_char = char
            elif char == "-":
                if not instring and (i + 1) < len(string) and string[i + 1] == "-":
                    return [(i, len(string))]
        return []
    
    @staticmethod
    def format(string):
        """ Used to formant multiple lines in haskell """
        return ":{\n"+string+"\n:}\n"

    @classmethod
    def stop_sound(cls):
        """ Triggers the 'hush' command using Ctrl+. """
        return "hush"

class StackTidalInterpreter(TidalInterpreter):
    path = "stack ghci"

# Interpreters over OSC (e.g. Sonic Pi)
# -------------------------------------

class OSCInterpreter(Interpreter):
    """ Class for sending messages via OSC instead of using a subprocess """
    def __init__(self, *args, **kwargs):
        self.re = {"tag_bold": self.find_keyword, "tag_italic": self.find_comment}
        self.lang = OSC.OSCClient()
        self.lang.connect((self.host, self.port))
        self._osc_error = False

    # Overload to not activate a server
    def start(self):
        return self

    def kill(self):
        self.evaluate(self.stop_sound())
        self.lang.close()
        return

    def new_osc_message(self, string):
        """ Overload in sub-class, return OSC.OSCMessage"""
        return

    def print_osc_warning_message(self):
        print("Warning: No connection made to local {} OSC server instance.".format(self.__repr__()))
        return

    def evaluate(self, string, *args, **kwargs):
        # Print to the console the message
        Interpreter.print_stdin(self, string, *args, **kwargs)
        # Create an osc message and send to the server
        try:
            self.lang.send(self.new_osc_message(string))
            self._osc_error = False
        except OSC.OSCClientError:
            if not self._osc_error:
                self.print_osc_warning_message()
            self._osc_error = True
        return

class SuperColliderInterpreter(OSCInterpreter):
    filetype = ".scd"
    host = 'localhost'
    port = 57120
    name = "SuperCollider"

    def new_osc_message(self, string):
        """ Returns OSC message for Troop Quark """
        msg = OSC.OSCMessage("/troop")
        msg.append([string])
        return msg

    @classmethod
    def find_comment(cls, string):        
        instring, instring_char = False, ""
        for i, char in enumerate(string):
            if char in ('"', "'"):
                if instring:
                    if char == instring_char:
                        instring = False
                        instring_char = ""
                else:
                    instring = True
                    instring_char = char
            elif char == "/":
                if not instring and i < len(string) and string[i + 1] == "/":
                    return [(i, len(string))]
        return []

    @classmethod
    def get_block_of_code(cls, text, index):
        """ Returns the start and end line numbers of the text to evaluate when pressing Ctrl+Return. """

        # Get start and end of the buffer
        start, end = "1.0", text.index("end")
        lastline   = int(end.split('.')[0]) + 1

        # Indicies of block to execute
        block = [0,0]        
        
        # 1. Get position of cursor
        cur_y, cur_x = index.split(".")
        cur_y, cur_x = int(cur_y), int(cur_x)

        left_cur_y, left_cur_x   = cur_y, cur_x
        right_cur_y, right_cur_x = cur_y, cur_x

        # Go back to find a left bracket

        while True:

            new_left_cur_y,  new_left_cur_x  = cls.get_left_bracket(text, left_cur_y, left_cur_x)
            new_right_cur_y, new_right_cur_x = cls.get_right_bracket(text, right_cur_y, right_cur_x)

            if new_left_cur_y is None or new_right_cur_y is None:

                block = [left_cur_y, right_cur_y + 1]

                break

            else:

                left_cur_y,  left_cur_x  = new_left_cur_y,  new_left_cur_x
                right_cur_y, right_cur_x = new_right_cur_y, new_right_cur_x

        return block

    @classmethod
    def get_left_bracket(cls, text, cur_y, cur_x):
        count = 0
        line_text = text.get("{}.{}".format(cur_y, 0), "{}.{}".format(cur_y, "end"))
        for line_num in range(cur_y, 0, -1):
            # Only check line if it has text
            if len(line_text) > 0:
                for char_num in range(cur_x - 1, -1, -1):
                    
                    try:
                        char = line_text[char_num] 
                    except IndexError as e:
                        print("left bracket, string is {}, index is {}".format(line_text, char_num))
                        raise(e)

                    if char == ")":
                        count += 1
                    elif char == "(":
                        if count == 0:
                            return line_num, char_num
                        else:
                            count -= 1
            line_text = text.get("{}.{}".format(line_num - 1, 0), "{}.{}".format(line_num - 1, "end"))
            cur_x     = len(line_text)
        return None, None

    @classmethod
    def get_right_bracket(cls, text, cur_y, cur_x):
        num_lines = int(text.index("end").split(".")[0]) + 1
        count = 0
        for line_num in range(cur_y, num_lines):
            line_text = text.get("{}.{}".format(line_num, 0), "{}.{}".format(line_num, "end"))
            # Only check line if it has text
            if len(line_text) > 0:
                for char_num in range(cur_x, len(line_text)):
                    
                    try:
                        char = line_text[char_num] 
                    except IndexError as e:
                        print("right bracket, string is {}, index is {}".format(line_text, char_num))
                        raise(e)

                    if char == "(":
                        count += 1
                    if char == ")":
                        if count == 0:
                            return line_num, char_num + 1
                        else:
                            count -= 1
            cur_x = 0
        else:
            return None, None

    @classmethod
    def stop_sound(cls):
        return "s.freeAll"


class SonicPiInterpreter(OSCInterpreter):
    filetype = ".rb"
    host = 'localhost'
    port = 4557
    name = "Sonic-Pi"

    def new_osc_message(self, string):
        """ Returns OSC message for Sonic Pi """
        msg = OSC.OSCMessage("/run-code")
        msg.append(["0", string])
        return msg

    @classmethod
    def find_comment(cls, string):        
        instring, instring_char = False, ""
        for i, char in enumerate(string):
            if char in ('"', "'"):
                if instring:
                    if char == instring_char:
                        instring = False
                        instring_char = ""
                else:
                    instring = True
                    instring_char = char
            elif char == "#":
              if not instring:
                  return [(i, len(string))]
        return []

    @classmethod
    def get_block_of_code(cls, text, index):
        """ Returns first and last line as Sonic Pi evaluates the whole code """
        start, end = "1.0", text.index("end")
        return [int(index.split(".")[0]) for index in (start, end)]

    @classmethod
    def stop_sound(cls):
        return 'osc_send({!r}, {}, "/stop-all-jobs")'.format(cls.host, cls.port)

        
# Set up ID system

langtypes = { FOXDOT        : FoxDotInterpreter,
              TIDAL         : TidalInterpreter,
              TIDALSTACK    : StackTidalInterpreter,
              SUPERCOLLIDER : SuperColliderInterpreter,
              SONICPI       : SonicPiInterpreter,
              DUMMY         : DummyInterpreter }

for lang_id, lang_cls in langtypes.items():
    lang_cls.id = lang_id