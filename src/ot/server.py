class MemoryBackend(object):
    """Simple backend that saves all operations in the server's memory. This
    causes the processe's heap to grow indefinitely.
    """

    def __init__(self, operations=[]):
        self.operations = operations[:]
        self.last_operation = {}

    def save_operation(self, user_id, operation):
        """Save an operation in the database."""
        self.last_operation[user_id] = len(self.operations)
        self.operations.append(operation)

    def get_operations(self, start, end=None):
        """Return operations in a given range."""
        return self.operations[start:end]

    def get_last_revision_from_user(self, user_id):
        """Return the revision number of the last operation from a given user."""
        return self.last_operation.get(user_id, None)


class Server(object):
    """Receives operations from clients, transforms them against all
    concurrent operations and sends them back to all clients.
    """

    def __init__(self, document, backend):
        self.document = document
        self.backend = backend

    def receive_operation(self, user_id, revision, operation):
        """Transforms an operation coming from a client against all concurrent
        operation, applies it to the current document and returns the operation
        to send to the clients.
        """

        last_by_user = self.backend.get_last_revision_from_user(user_id)
        if last_by_user and last_by_user >= revision:
            return

        Operation = operation.__class__

        concurrent_operations = self.backend.get_operations(revision)
        for concurrent_operation in concurrent_operations:
            (operation, _) = Operation.transform(operation, concurrent_operation)

        self.document = operation(self.document)
        self.backend.save_operation(user_id, operation)
        return operation
