# I have adopted the naming convention from Daniel Spiewak's CCCP:
# https://github.com/djspiewak/cccp/blob/master/agent/src/main/scala/com/codecommit/cccp/agent/state.scala


class Client(object):
    """Handles the client part of the OT synchronization protocol. Transforms
    incoming operations from the server, buffers operations from the user and
    sends them to the server at the right time.
    """

    def __init__(self, revision):
        self.revision = revision
        self.state = synchronized

    def apply_client(self, operation):
        """Call this method when the user (!) changes the document."""
        self.state = self.state.apply_client(self, operation)

    def apply_server(self, operation):
        """Call this method with a new operation from the server."""
        self.revision += 1
        self.state = self.state.apply_server(self, operation)

    def server_ack(self):
        """Call this method when the server acknowledges an operation send by
        the current user (via the send_operation method)
        """
        self.revision += 1
        self.state = self.state.server_ack(self)

    def send_operation(self, revision, operation):
        """Should send an operation and its revision number to the server."""
        raise NotImplementedError("You have to override 'send_operation' in your Client child class")

    def apply_operation(self, operation):
        """Should apply an operation from the server to the current document."""
        raise NotImplementedError("You have to overrid 'apply_operation' in your Client child class")


class Synchronized(object):
    """In the 'Synchronized' state, there is no pending operation that the client
    has sent to the server.
    """

    def apply_client(self, client, operation):
        # When the user makes an edit, send the operation to the server and
        # switch to the 'AwaitingConfirm' state
        client.send_operation(client.revision, operation)
        return AwaitingConfirm(operation)

    def apply_server(self, client, operation):
        # When we receive a new operation from the server, the operation can be
        # simply applied to the current document
        client.apply_operation(operation)
        return self

    def server_ack(self, client):
        raise RuntimeError("There is no pending operation.")


# Singleton
synchronized = Synchronized()


class AwaitingConfirm(object):
    """In the 'awaitingConfirm' state, there's one operation the client has sent
    to the server and is still waiting for an acknowledgement.
    """

    def __init__(self, outstanding):
        # Save the pending operation
        self.outstanding = outstanding

    def apply_client(self, client, operation):
        # When the user makes an edit, don't send the operation immediately,
        # instead switch to the 'AwaitingWithBuffer' state
        return AwaitingWithBuffer(self.outstanding, operation)

    def apply_server(self, client, operation):
        #                   /\
        # self.outstanding /  \ operation
        #                 /    \
        #                 \    /
        #  operation_p     \  / outstanding_p (new self.outstanding)
        #  (can be applied  \/
        #  to the client's
        #  current document)
        Operation = self.outstanding.__class__
        (outstanding_p, operation_p) = Operation.transform(self.outstanding, operation)
        client.apply_operation(operation_p)
        return AwaitingConfirm(outstanding_p)

    def server_ack(self, client):
        return synchronized


class AwaitingWithBuffer(object):
    """In the 'awaitingWithBuffer' state, the client is waiting for an operation
    to be acknowledged by the server while buffering the edits the user makes
    """

    def __init__(self, outstanding, buffer):
        # Save the pending operation and the user's edits since then
        self.outstanding = outstanding
        self.buffer = buffer

    def apply_client(self, client, operation):
        # Compose the user's changes onto the buffer
        newBuffer = self.buffer.compose(operation)
        return AwaitingWithBuffer(self.outstanding, newBuffer)

    def apply_server(self, client, operation):
        #                       /\
        #     self.outstanding /  \ operation
        #                     /    \
        #                    /\    /
        #       self.buffer /  \* / outstanding_p
        #                  /    \/
        #                  \    /
        #      operation_pp \  / buffer_p
        #                    \/
        # the transformed
        # operation -- can
        # be applied to the
        # client's current
        # document
        #
        # * operation_p
        Operation = self.outstanding.__class__
        (outstanding_p, operation_p) = Operation.transform(self.outstanding, operation)
        (buffer_p, operation_pp) = Operation.transform(self.buffer, operation_p)
        client.apply_operation(operation_pp)
        return AwaitingWithBuffer(outstanding_p, buffer_p)

    def server_ack(self, client):
        # The pending operation has been acknowledged
        # => send buffer
        client.send_operation(client.revision, self.buffer)
        return AwaitingConfirm(self.buffer)
