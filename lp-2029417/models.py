from twisted.protocols import amp
from utils import deferWithTimeout

undefined = object()


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


class Client:
    """Wrapper around an :class:`amp.AMP` instance.

    Limits the API to a subset of the behaviour of :class:`amp.AMP`'s,
    with alterations to make it suitable for use from a thread outside
    of the reactor.
    """

    def __init__(self, conn):
        super().__init__()
        self._conn = conn

    def __call__(self, cmd, *args, **kwargs):
        """Call a remote RPC method.

        This is how the client is normally used.

        :note:
            Though the call signature shows positional arguments, their use is
            an error. They're in the signature is so this method can detect
            them and provide a better error message than that from Python.
            Python's error message when arguments don't match the call's
            signature is not great at best, but it also makes it hard to
            figure out the receiver when the `TypeError` is raised in a
            different stack from the caller's, e.g. when calling into the
            Twisted reactor from a thread.

        :param cmd: The `amp.Command` child class representing the remote
            method to be invoked.
        :param kwargs: Any parameters to the remote method.  Only keyword
            arguments are accepted.
        :return: A deferred result.  Call its `wait` method (with a timeout
            in seconds) to block on the call's completion.
        """
        if len(args) != 0:
            receiver_name = "{}.{}".format(
                self.__module__,
                self.__class__.__name__,
            )
            raise TypeError(
                "%s called with %d positional arguments, %r, but positional "
                "arguments are not supported. Usage: client(command, arg1="
                "value1, ...)" % (receiver_name, len(args), args)
            )

        timeout = kwargs.pop("_timeout", undefined)
        if timeout is undefined:
            timeout = 120  # 2 minutes
        if timeout is None or timeout <= 0:
            # Uncomment for the fix
            return self._conn.callRemote(cmd, **kwargs)#.addErrback(lambda x: self._conn.transport.loseConnection())
        else:
            return deferWithTimeout(
                timeout, self._conn.callRemote, cmd, **kwargs
            )#.addErrback(lambda x: self._conn.transport.loseConnection())