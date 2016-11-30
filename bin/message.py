"""
    Server/message.py
    -----------------

    Messages are sent as a series of arguments surrounnded by
    <arrows><like><so>.

"""

import re

re_msg = re.compile(r"<(.*?>?)>", re.DOTALL)

class NetworkMessage:
    def __init__(self, string):
        self.data = re_msg.findall(string)
        self.raw_string = string

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

if __name__ == "__main__":

    test = NetworkMessage("<t><1><0><999>")
    print test
    print NetworkMessage.compile(1, *test)
