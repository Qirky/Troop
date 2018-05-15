from functools import partial

class _constraint(object):
    def __init__(self, text):
        self.text = text

        self.constraints = {
            "communism"    : self.communism,
            "anarchy"      : self.anarchy,
            "democracy"    : self.democracy,
            "dictatorship" : self.dictatorship
        }

        self.using = {name: False for name in self.constraints}
        self.leader = None

        self.set_constraint("anarchy")

    def __call__(self):
        """ If there are multuple users connected, start to apply rules"""
        return self.rule() if len(self.text.peers) > 1 else True

    def names(self):
        return self.constraints.keys()

    def current(self):
        return [name for name, value in self.using if value is True][0]

    def set_constraint(self, name, peer_id=None):
        """  """
        self.rule = self.constraints[name]
        if peer_id is not None:
            self.leader = self.text.peers[peer_id]
        return
    
    def get_count(self, func=sum):
        """ Performs `func` (default is `sum`) on the list of all peer char totals  """
        return float(func([peer.count for peer in self.text.peers.values()]))

    def anarchy(self, *args, **kwargs):
        """ Anything goes! """
        return True

    def democracy(self, *args, **kwargs):
        """ No peer can have more than 50% share of the text (min 10 chars) """
        if self.master.text.marker.count > 10:
            max_chars = self.get_count(text.peers) / len(text.peers)
            if self.text.marker.count > max_chars:
                return False
        return True

    def communism(self, *args, **kwargs):
        """ All peers must enter the same amount of text """
        return self.text.marker.count <= self.get_count(min) + 1

    def dictatorship(self, *args, **kwargs):
        """ The dictator can put in chars but other peers can  """
        return True if self.text.marker == self.leader else (self.text.marker.count < (self.get_count() * 0.25) / (len(self.text.peers) - 1))



# class _constraint(object):
#     def __init__(self, master=None):
#         self.master = master
#     def __call__(self, text, *args):
#         if len(text.peers) > 1:
#             return self.rule(text, *args)
#         return True

# class anarchy(_constraint):
#     """ No rule (anarchy) """
#     def rule(self, *args, **kwargs):
#         return True

# class democracy(_constraint):
#     """ Users can not enter more than 1/n-1 of the text i.e. if 3 users are connected,
#         a user cannot enter over 1/2 of the total number of characters """
#     def rule(self, text, *args):
#         if text.marker.count > 10:
#             max_chars = self.get_count(text.peers) / len(text.peers)
#             if text.marker.count > max_chars:
#                 return False
#         return True

# class communism(_constraint):
#     """ Users can only add a maximum of 1 character more than anyone else.
#     i.e. everyone has to be the same number of characters """
#     def rule(self, text, *args):
#         return text.marker.count <= self.get_count(text.peers, min) + 1

# class dictatorship(_constraint):
#     """ One user (master) can use any number of the characters but other users
#         can only use 25/(n-1) % """
#     def rule(self, text, peer, *args):
#         if peer != text.peers[self.master]:
#             return peer.count < (self.get_count(text.peers) * 0.25) / (len(text.peers) - 1)
