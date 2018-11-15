from functools import partial

try:
    from Tkinter import BooleanVar
except ImportError:
    from tkinter import BooleanVar

def get_count(text, func=sum):
    """ Performs `func` (default is `sum`) on the list of all peer char totals  """
    return float(func([peer.count for peer in text.peers.values()]))

class TextConstraint(object):
    def __init__(self, text):
        self.text = text

        self.constraints = {
            0 : anarchy(),
            1 : communism(),
            2 : democracy(),
            3 : dictatorship()
        } 
        
        self.leader        = None
        self.constraint_id = None
        self.rule          = lambda *args: True

        self.using = { n: BooleanVar() for n in self.constraints }

        self.set_constraint(0)

    def __call__(self):
        """ If there are multuple users connected, start to apply rules"""
        return self.rule(self.text)

    def __eq__(self, constraint_id):
        return self.constraint_id == constraint_id

    def __ne__(self, constraint_id):
        return self.constraint_id != constraint_id

    def names(self):
        return [str(c) for c in self.constraints.keys()]

    def items(self):
        return self.constraints.items()

    def get_name(self, n):
        return self.constraints[n]

    def get_id(self, name):
        for n, constraint in self.constraints.items():
            if name == str(constraint):
                return n
        else:
            raise KeyError("Key {!r} not found".format(n))

    def set_constraint(self, constraint_id, peer_id=None):
        """  """
        self.constraint_id = constraint_id
        
        self.rule = self.constraints[constraint_id]
        
        if peer_id is not None and peer_id >= 0:
            self.leader = self.text.peers[peer_id]
        else:
            self.leader = None
        
        for n in self.constraints:
            if n == constraint_id:
                self.using[n].set(True)
            else:
                self.using[n].set(False)
        return

# Constraints
    
class __constraint(object):
    def __init__(self):
        pass
    
    def __repr__(self):
        return self.__class__.__name__

    def __call__(self, text, *args):
        if len(text.peers) > 1:
            return self.rule(text, *args)
        return True

class anarchy(__constraint):
    """ No rule (anarchy) """
    def rule(self, *args, **kwargs):
        return True

class democracy(__constraint):
    """ Users can not enter more than 1/n-1 of the text i.e. if 3 users are connected,
        a user cannot enter over 1/2 of the total number of characters """
    def rule(self, text, *args):
        if text.marker.count > 10:
            max_chars = get_count(text) / len(text.peers)
            if text.marker.count > max_chars:
                return False
        return True

class communism(__constraint):
    """ Users can only add a maximum of 1 character more than anyone else.
    i.e. everyone has to be the same number of characters """
    def rule(self, text, *args):
        return text.marker.count <= get_count(text, min) + 1

class dictatorship(__constraint):
    """ One user (master) can use any number of the characters but other users
        can only use 25/(n-1) % """
    def rule(self, text, peer, leader, *args):
        if peer != text.peers[leader]:
            return peer.count < (get_count(text) * 0.25) / (len(text.peers) - 1)
