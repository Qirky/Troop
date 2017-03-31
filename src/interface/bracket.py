from Tkinter import *
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

    def __call__(self, char, row, col, reply):

        ret = None

        insert = "%d.%d" % (row, col)

        # 1. Type a left bracket

        next_char = self.text.get(insert)

        if char in self.left_brackets:

            # Insert

            self.root.push_queue.put( MSG_INSERT(-1, char, row, col, reply) )

            # Needs a closing bracket

            if next_char in whitespace + self.right_brackets.keys():

                # Add a bracket and it's closing bracket but move the  cursor to *inside* the brackets

                self.root.push_queue.put( MSG_INSERT(-1, self.left_brackets[char], row, col + 1, reply) )

                self.root.push_queue.put( MSG_SET_MARK(-1, row, col + 1, reply) )

                ret = "break"

            # Update line colours
        
            self.root.colour_line(row)

        # 2. Type right bracket
        elif char in self.right_brackets:

            # Add the bracket, and delete later if we don't need it

            all_text = [""] + self.text.get("1.0", END).split("\n")[:-1]

            all_text[row] = all_text[row][:col] + char + all_text[row][col:]

            # Insert bracket

            # self.root.push_queue.put( MSG_INSERT(-1, char, row, col, reply) )

            # self.root.push_queue.put( MSG_SET_MARK(-1, row, col + 1, reply) )

            # Find its starting bracket

            coords = self.find_starting_bracket(all_text, row, col - 1, char)

            if coords is not None:

                # Assume we are adding a new bracket

                adding_bracket = True

                # Get index of the end of the buffer

                col1 = new_col = (col + 1) if (col < len(all_text[row])-1) else 0
                row1 = new_row = (row + 1) if new_col == 0 else row

                end_row, end_col = len(all_text), 0

                while (new_row, new_col) != (end_row, end_col) and len(all_text[new_row]) > 0:

                    # If we find a closing bracket, find it's pair

                    next_char = all_text[new_row][new_col]

                    # stdout(repr(all_text[new_row]), new_row, new_col )

                    if next_char == char:

                        coords_ = self.find_starting_bracket(all_text, new_row, new_col, char, offset=0)

                        # If there is not a closing brackets

                        if coords_ is None:

                            adding_bracket = False

                            break

                        else:

                            adding_bracket = True

                    else:

                        break

                    # row1, col1 = new_row, new_col
                    
                    if new_col == (len(all_text[new_row])-1):
                        
                        new_row += 1
                        new_col  = 0

                    else:

                        new_col += 1
                    
                if not adding_bracket:

                    # self.root.push_queue.put( MSG_DELETE(-1, row, col, reply) )

                    self.root.push_queue.put( MSG_SET_MARK(-1, row, col + 1, reply) ) # Move marker

                else:

                    self.root.push_queue.put( MSG_INSERT(-1, char, row, col, reply) )

                 # Update line colours
                
                self.root.colour_line(row)

                # Highlight brackets

                if coords is not None:

                    # Define coords of brackets
                    
                    row1, col1 = coords
                    row2, col2 = row, col

                    # Send this as a message

                    self.root.push_queue.put( MSG_BRACKET(-1, row1, col1, row2, col2, reply))

            else:

                self.root.push_queue.put( MSG_INSERT(-1, char, row, col, reply) )

        return
                                 

    def find_starting_bracket(self, text, line, column, bracket_style, offset = 0):
        """ Finds the opening bracket to the closing bracket at line, column co-ords.
            Returns None if not found. """
       
        line_length = column + 1
        used_br = offset

        for row in range(line, 0, -1):

            if line_length > 1:

                for col in range(line_length-1, -1, -1): # line_length - 1?

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
