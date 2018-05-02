# def new_operation(index, value, tail):
#     """ Returns an operation as a list and removes index/tail if they are 0 """
#     operation = []
#     if index > 0:
#         operation.append(index)
#     operation.append(value)
#     if tail > 0:
#         operation.append(tail)
#     return operation

def _is_retain(op):
    return isinstance(op, int) and op > 0

def _is_delete(op):
    return isinstance(op, int) and op < 0

def _is_insert(op):
    return isinstance(op, str)

def new_operation(*args):
    """ Returns an operation as a list and removes index/tail if they are 0 """
    values = args[:-1]
    length = args[-1]

    operation = []

    for value in values:

        if value != 0:
       
            operation.append(value)

            if isinstance(value, int):

                if value > 0:

                    length -= value

                else:

                    length += value
    
    if length > 0:
    
        operation.append(length)

    elif _is_retain(operation[-1]):

        # Trim the final retain

        operation[-1] += length

    if operation[-1] == 0:

        operation.pop()
    
    return operation

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

def get_operation_size(ops):
    """ Returns the number of characters added by an operation (can be negative) """
    count = 0
    for op in ops:
        if isinstance(op, str):
            count += len(op)
        elif isinstance(op, int) and op < 0:
            count += op
    return count


def get_doc_size(ops):
    """ Returns the size of the document this operation is operating on """
    total = 0
    for value in ops:
        if _is_retain(value):
            total += value
        elif _is_delete(value):
            total += (value * -1)
    return total

import re
def get_peer_locs(n, text):
    return ( (match.start(), match.end()) for match in re.finditer("{}+".format(n), text))

import string
def get_peer_char(id_num):
    return str((string.digits + string.ascii_letters)[id_num])


if __name__ == '__main__':
    op = [5, "a", 2]

    print(get_operation_index(op))
    print(get_marker_location(op))