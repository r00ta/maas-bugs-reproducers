from twisted.internet.defer import Deferred
from twisted.protocols import amp

from models import Ping


class RPCProtocol(amp.AMP):
    """A specialisation of `amp.AMP`.

    It's hard to track exactly when an `amp.AMP` protocol is connected to its
    transport, or disconnected, from the "outside". It's necessary to subclass
    and override `connectionMade` and `connectionLost` and signal from there,
    which is what this class does.

    :ivar onConnectionMade: A `Deferred` that fires when `connectionMade` has
        been called, i.e. this protocol is now connected.
    :ivar onConnectionLost: A `Deferred` that fires when `connectionLost` has
        been called, i.e. this protocol is no longer connected.
    """

    def __init__(self):
        super().__init__()
        self.onConnectionMade = Deferred()
        self.onConnectionLost = Deferred()

    def connectionMade(self):
        super().connectionMade()
        self.onConnectionMade.callback(None)

    def connectionLost(self, reason):
        super().connectionLost(reason)
        self.onConnectionLost.callback(None)

    def _sendBoxCommand(self, command, box, requiresAnswer=True):
        """Override `_sendBoxCommand` to log the sent RPC message."""
        box[amp.COMMAND] = command
        return super()._sendBoxCommand(
            command, box, requiresAnswer=requiresAnswer
        )

    def unhandledError(self, failure):
        """Terminal errback, after application code has seen the failure.

        `amp.BoxDispatcher.unhandledError` calls the `amp.IBoxSender`'s
        `unhandledError`. In the default implementation this disconnects the
        transport.

        Here we instead log the failure but do *not* disconnect because it's
        too disruptive to the running of MAAS.
        In case of https://bugs.launchpad.net/maas/+bug/2029417, we drop the connection instead.
        """
        print("There is an unhandledError, let's see.")
        if (
                failure.check(RuntimeError)
                and "the handler is closed" in failure.getErrorMessage()
        ):
            # This should call self.transport.loseConnection()
            super().unhandledError(failure)
            print(
                "XXX The handler is closed and the exception was unhandled. The connection is dropped."
            )
        else:
            print(
                failure,
                (
                    "XXX Unhandled failure during AMP request. This is probably a bug. "
                    "Please ensure that this error is handled within application "
                    "code."
                ),
            )

    @Ping.responder
    def ping(self):
        """ping()

        Implementation of
        :py:class:`~provisioningserver.rpc.common.Ping`.
        """
        return {}
