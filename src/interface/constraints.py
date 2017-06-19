class _constraint(object):
    def __init__(self, master=None):
        self.master = master
    def __call__(self, text, *args):
        if len(text.peers) > 1:
            return self.rule(text, *args)
        return True
    @staticmethod
    def get_count(peers, func=sum):
        return float(func([peer.count for peer in peers.values()]))

class anarchy(_constraint):
    """ No rule (anarchy) """
    def rule(self, *args, **kwargs):
        return True

class democracy(_constraint):
    """ Users can not enter more than 1/n-1 of the text i.e. if 3 users are connected,
        a user cannot enter over 1/2 of the total number of characters """
    def rule(self, text, *args):
        if text.marker.count > 10:
            max_chars = self.get_count(text.peers) / len(text.peers)
            if text.marker.count > max_chars:
                return False
        return True

class communism(_constraint):
    """ Users can only add a maximum of 1 character more than anyone else.
    i.e. everyone has to be the same number of characters """
    def rule(self, text, *args):
        return text.marker.count <= self.get_count(text.peers, min) + 1

class dictatorship(_constraint):
    """ One user (master) can use any number of the characters but other users
        can only use 25/(n-1) % """
    def rule(self, text, peer, *args):
        if peer != text.peers[self.master]:
            return peer.count < (self.get_count(text.peers) * 0.25) / (len(text.peers) - 1)
