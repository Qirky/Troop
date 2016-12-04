"""
    Server/message.py
    -----------------

    Messages are sent as a series of arguments surrounnded by
    <arrows><like><so>.

"""

import re

re_msg = re.compile(r"<(.*?>?)>(?=<|$)", re.DOTALL)

# Message Types

MSG_CONNECT   = 1
MSG_INSERT    = 2
MSG_DELETE    = 3
MSG_BACKSPACE = 4
MSG_SELECT    = 5
MSG_EVALUATE  = 6
MSG_HIGHLIGHT = 7
MSG_GET_ALL   = 8
MSG_SET_ALL   = 9
MSG_RESPONSE  = 10
MSG_REMOVE    = 11

class NetworkMessage:
    """
        Messages are in the form <type><id>(*<data>)
    """
    def __init__(self, string):
        self.data = re_msg.findall(string)

        if len(self.data) == 0:

            raise EmptyMessageError
        
        self.raw_string = string
        self.type  = int(self.data[0]) # Int
        self.id    = int(self.data[1]) # Source ID
        self.data  = self.data[1:]     # Data objects

    def __repr__(self):
        return repr(self.data)

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        for item in self.data:
            yield item

    def __getitem__(self, key):
        return self.data[key]

    def insert(self, item, index=0):
        self.data.insert(item, index)
        return self

    @staticmethod
    def compile(*args):
        return "".join(["<{}>".format(item) for item in args])

    @staticmethod
    def password(password):
        return NetworkMessage.compile(-1, -1, password)


class EmptyMessageError:
    def __init__(self):
        self.value = "Message contained no data"
    def __str__(self):
        return repr(self.value)

class ConnectionError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    

if __name__ == "__main__":

    pass
