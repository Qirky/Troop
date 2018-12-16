# Connection error flags

ERR_LOGIN_FAIL = -1
ERR_MAX_LOGINS = -2
ERR_NAME_TAKEN = -3

# List of all the possible characters used to represent peers in the document

import string

PEER_CHARS = list(string.digits + string.ascii_letters)

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

    elif len(operation) and _is_retain(operation[-1]):

        # Trim the final retain

        operation[-1] += length

    if len(operation) and operation[-1] == 0:

        operation.pop()
    
    return operation

def get_operation_index(ops):
    """ Returns the index that a marker should be *after* an operation """

    # If the last operation is a "skip", offset the index or 
    # else it just moves it to the end of the document
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

def empty_operation(ops):
    """ Returns True if the operation is an empty list or only contains positive integers """
    return (ops == [] or all([isinstance(x, int) and (x > 0) for x in ops]))

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

def get_peer_char(id_num):
    """ Returns the ID character to identify a peer """
    return PEER_CHARS[id_num]

def get_peer_id_from_char(char):
    """ Returns the numeric index for a ID character """
    return PEER_CHARS.index(str(char))
