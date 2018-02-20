from __future__ import absolute_import

try:
    from Tkinter import *
except ImportError:
    from tkinter import *

from ..message import *
from ..config  import *

whitespace = [" ","\t","\n","\r","\f","\v"]

class BracketHandler:
    def __init__(self, master):

        self.root = master
        
        self.text = master.text

        self.inbrackets = False

        self.style = {'borderwidth': 2, 'relief' : 'groove'}
        self.text.tag_config("tag_open_brackets", **self.style)

        left_b  = list("([{")
        right_b = list(")]}")

        self.left_brackets  = dict(zip(left_b, right_b))
        self.right_brackets = dict(zip(right_b, left_b))

        self.left_brackets_all  = dict(list(zip(left_b, right_b)) + [("'","'"), ('"','"')])
        self.right_brackets_all = dict(list(zip(right_b, left_b)) + [("'","'"), ('"','"')])


    def is_inserting_bracket(self, text, row, col, char):

        # Assume we are adding a new bracket

        adding_bracket = True

        coords = self.find_starting_bracket(text, row, col - 1, char)

        # If there isn't a starting bracket

        if coords is not None:

            # Get index of the end of the buffer

            col1 = new_col = (col + 1) if (col < len(text[row])-1) else 0
            row1 = new_row = (row + 1) if new_col == 0 else row

            end_row, end_col = len(text), 0

            while (new_row, new_col) != (end_row, end_col) and len(text[new_row]) > 0:

                # If we find a closing bracket, find it's pair

                next_char = text[new_row][new_col]

                if next_char == char:

                    coords_ = self.find_starting_bracket(text, new_row, new_col - 1, char, offset=0)

                    # If there is not a closing brackets

                    if coords_ is None:

                        adding_bracket = False

                        break

                    else:

                        adding_bracket = True

                else:

                    break

                # row1, col1 = new_row, new_col
                
                if new_col == (len(text[new_row])-1):
                    
                    new_row += 1
                    new_col  = 0

                else:

                    new_col += 1

        return adding_bracket


    def find_starting_bracket(self, text, line, column, bracket_style, offset = 0):
        """ Finds the opening bracket to the closing bracket at line, column co-ords.
            Returns None if not found. """
       
        line_length = column + 1
        used_br = offset

        for row in range(line, 0, -1):

            if line_length > 1:

                for col in range(line_length-1, -1, -1):

                    # If the char is a left bracket and not used, break

                    try:

                        if text[row][col] == self.right_brackets[bracket_style]:

                            if used_br == 0:

                                return row, col

                            else:

                                used_br -= 1

                        elif text[row][col] == bracket_style:

                            used_br += 1

                    except IndexError: # TODO <- tidy this up

                        stdout(text[row], col, len(text[row]), line_length)

            # line_length = int(self.text.index("{}.end".format(row-1)).split(".")[1])
            line_length = len(text[row-1])

        else:

            return None
