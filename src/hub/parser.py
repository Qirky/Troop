class HubParser(dict):
    def __init__(self, input):
        super().__init__()
        if '@' in input:
            self['name'], address = input.split('@', 1)
            if ':' in address:
                self['host'], self['port'] = address.split(':', 1)
            else:
                self['host'] = address
        else:
            self['name'] = input
