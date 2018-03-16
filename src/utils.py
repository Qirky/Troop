def new_operation(index, value, tail):
    """ Returns an operation as a list and removes index/tail if they are 0 """
    operation = []
    if index > 0:
        operation.append(index)
    operation.append(value)
    if tail > 0:
        operation.append(tail)
    return operation

def get_marker_location(ops):
    """ Returns the index nubmer a marker should be at based on its operation """
    n = 0
    for op in ops:
        if isinstance(op, str):
            n += len(op)
            break
        elif isinstance(op, int):
            if op >= 0:
                n += op
            else:
                break
    return n

def get_operation_size(ops):
    for op in ops:
        if isinstance(op, str):
            return len(op)
        elif isinstance(op, int) and op < 0:
            return op

import re
def get_peer_locs(n, text):
    return ( (match.start(), match.end()) for match in re.finditer("{}+".format(n), text))