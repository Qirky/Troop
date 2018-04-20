# def new_operation(index, value, tail):
#     """ Returns an operation as a list and removes index/tail if they are 0 """
#     operation = []
#     if index > 0:
#         operation.append(index)
#     operation.append(value)
#     if tail > 0:
#         operation.append(tail)
#     return operation


def new_operation(index, *args):
    """ Returns an operation as a list and removes index/tail if they are 0 """
    values = args[:-1]
    length = args[-1]

    operation = []

    if index > 0:
    
        operation.append(index)

        length -= index

    for value in values:
       
        operation.append(value)

        if isinstance(value, int):

            if value > 0:

                length -= value

            else:

                length += value
    
    if length > 0:
    
        operation.append(length)
    
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
    """ Returns the number of characters added by an operation (can be negative) """
    count = 0
    for op in ops:
        if isinstance(op, str):
            count += len(op)
        elif isinstance(op, int) and op < 0:
            count += op
    return count

def get_operation_index(ops):
    """ Returns the index that a marker should be after an operation """
    if isinstance(ops[-1], int) and ops[-1] > 0:
        index = ops[-1] * -1
    else:
        index = 0
    for op in ops:
        if isinstance(op, int) and op > 0:
            index += op
        elif isinstance(op, str):
            index += len(op)
    return index

import re
def get_peer_locs(n, text):
    return ( (match.start(), match.end()) for match in re.finditer("{}+".format(n), text))