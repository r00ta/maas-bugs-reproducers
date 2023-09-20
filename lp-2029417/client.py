import time

from twisted.internet import reactor, protocol
from twisted.internet.task import LoopingCall

from models import Sum, Pippo, Ping
from rpc import RPCProtocol
from utils import deferWithTimeout


def execute_ping(session):
    session.callRemote(Ping).addCallback(lambda x: print("PING SUCCESS")).addErrback(lambda x: print("error in ping"))

    def _onFailure(failure):
        print(
            "Failure on ping dropping connection"
        )
        session.transport.loseConnection()

    deferWithTimeout(10, session.callRemote, Ping).addErrback(_onFailure)


def pingme(session):
    timer_service = LoopingCall(lambda: execute_ping(session))
    timer_service.start(10)  # Execute every 10 seconds


class MyAMPClientProtocol(RPCProtocol):

    def connectionMade(self):
        d = self.callRemote(Sum, a=10, b=20)
        d.addCallback(self.print_response)
        d.addErrback(self.print_error)
        pingme(self)

    def connectionLost(self, reason):
        super().connectionLost(reason)
        print("CONNECTION LOST " + str(reason))

    def print_response(self, result):
        print(f"Received response from server: {result}")

    def print_error(self, failure):
        print(f"Error occurred: {failure.getErrorMessage()}")

    @Pippo.responder
    def say_hello(self):
        print("HELLOOOO")
        time.sleep(10)
        return {'result': "Hello Pippo"}


class MyAMPClientFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return MyAMPClientProtocol()

    def clientConnectionFailed(self, connector, reason):
        print(f"Connection failed: {reason.getErrorMessage()}")
        # reactor.stop()


if __name__ == '__main__':
    reactor.connectTCP('localhost', 1234, MyAMPClientFactory())
    reactor.run()
