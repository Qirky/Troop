"""
    Interpreter
    -----------

    Runs a block of FoxDot code. Designed to be overloaded
    for other language communication

"""
from __future__ import absolute_import
from .config import *

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
import os.path

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
    def __init__(self, *args, **kwargs):
        self.re={}

    def __repr__(self):
        return repr(self.__class__.__name__)

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
    
    def stop_sound(self):
        """ Returns the string for stopping all sound in a language """
        return ""
    
    @staticmethod
    def format(string):
        """ Method to be overloaded in sub-classes for formatting strings to be evaluated """
        return str(string) + "\n"
    
class Interpreter(DummyInterpreter):
    lang     = None
    clock    = None
    bootstrap = None
    keyword_regex = compile_regex([])
    comment_regex = compile_regex([])
    stdout   = None
    stdout_thread = None
    filetype = ".txt"
    def __init__(self, path, args=""):

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

        # Load bootfile

        if self.bootstrap is not None:

            for line in self.bootstrap.split("\n"):

                self.lang.stdin.write(line.rstrip() + "\n")
                self.lang.stdin.flush()

        return self

    def get_path_as_string(self):
        """ Returns the executable input as a string """
        return " ".join(self.path)

    def find_keyword(self, string):
        return [(match.start(), match.end()) for match in self.keyword_regex.finditer(string)]

    def find_comment(self, string):
        return [(match.start(), match.end()) for match in self.comment_regex.finditer(string)]

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
                for stdout_line in iter(self.f_out.readline, ""):
                    sys.stdout.write(stdout_line.rstrip())                
                # clear tmpfile
                self.f_out.truncate(0)
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
    def __init__(self, args):
        Interpreter.__init__(self, self.path, args)

class FoxDotInterpreter(BuiltinInterpreter):
    filetype=".py"
    path = "{} -u -m FoxDot --pipe".format(PYTHON_EXECUTABLE)

    def setup(self):
        self.keywords = ["Clock", "Scale", "Root", "var", "linvar", '>>']
        self.keyword_regex = compile_regex(self.keywords)

    def __repr__(self):
        return "FoxDot"

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

    def stop_sound(self):
        return "Clock.clear()"

class TidalInterpreter(BuiltinInterpreter):
    path = 'ghci'
    filetype = ".tidal"

    def start(self):

        # Import boot up code

        from .boot.tidal import bootstrap

        self.bootstrap = bootstrap

        Interpreter.start(self)

        # Set any keywords e.g. d1 and $

        self.keywords  = ["d{}".format(n) for n in range(1,17)] # update
        self.keywords.extend( ["\$", "#", "hush"] )

        self.keyword_regex = compile_regex(self.keywords)

        # threading.Thread(target=self.stdout).start()
        
        return self

    def __repr__(self):
        return "TidalCycles"

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

    def stop_sound(self):
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

    def __repr__(self):
        return "SuperCollider"

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

    def get_block_of_code(self, text, index):
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

            new_left_cur_y,  new_left_cur_x  = self.get_left_bracket(text, left_cur_y, left_cur_x)
            new_right_cur_y, new_right_cur_x = self.get_right_bracket(text, right_cur_y, right_cur_x)

            if new_left_cur_y is None or new_right_cur_y is None:

                block = [left_cur_y, right_cur_y + 1]

                break

            else:

                left_cur_y,  left_cur_x  = new_left_cur_y,  new_left_cur_x
                right_cur_y, right_cur_x = new_right_cur_y, new_right_cur_x

        return block

    def get_left_bracket(self, text, cur_y, cur_x):
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

    def get_right_bracket(self, text, cur_y, cur_x):
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


    def stop_sound(self):
        return "s.freeAll"


class SonicPiInterpreter(OSCInterpreter):
    filetype = ".rb"
    host = 'localhost'
    port = 4557
    
    def __repr__(self):
        return "Sonic-Pi"

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

    def get_block_of_code(self, text, index):
        """ Returns first and last line as Sonic Pi evaluates the whole code """
        start, end = "1.0", text.index("end")
        return [int(index.split(".")[0]) for index in (start, end)]

    def stop_sound(self):
        return 'osc_send({!r}, {}, "/stop-all-jobs")'.format(self.host, self.port)

        

langtypes = { FOXDOT        : FoxDotInterpreter,
              TIDAL         : TidalInterpreter,
              TIDALSTACK    : StackTidalInterpreter,
              SUPERCOLLIDER : SuperColliderInterpreter,
              SONICPI       : SonicPiInterpreter,
              DUMMY         : DummyInterpreter }
