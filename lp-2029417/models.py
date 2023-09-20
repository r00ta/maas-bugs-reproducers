from twisted.protocols import amp


class Sum(amp.Command):
    arguments = [(b'a', amp.Integer()),
                 (b'b', amp.Integer())]
    response = [(b'total', amp.Integer())]


class Pippo(amp.Command):
    arguments = []
    response = [(b'result', amp.Unicode())]


class Ping(amp.Command):
    """Ensure the connection is still good.

    :since: 2.4
    """

    arguments = []
    response = []
    errors = []
