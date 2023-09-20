import asyncio

import uvloop
from twisted.internet import asyncioreactor

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
asyncioreactor.install()
print(f"Event loop implementation: {str(type(asyncio.get_event_loop_policy()))}")

from twisted.internet.task import LoopingCall

from models import Sum, Pippo, Client
from rpc import RPCProtocol
from twisted.internet.endpoints import TCP6ServerEndpoint
from utils import deferWithTimeout

class SessionManager:
    def __init__(self):
        self.sessions = []

    def add(self, session):
        self.sessions.append(session)

    def remove(self, session):
        self.sessions.remove(session)

    def get_first_session(self):
        if self.sessions:
            print(f"+ There are {len(self.sessions)} sessions")
            return self.sessions[0]
        return None


def print_pippo_response(response):
    print("Received response for 'Pippo' command:", response)


def execute_pippo(client):
    if client:
        print("+ calling Pippo RPC procedure")
        # try:
        client(Pippo).addCallback(print_pippo_response)
        # deferWithTimeout(
        #     5, session.callRemote, Pippo
        # ).addCallback(print_pippo_response)
        # except Exception as e:
        #     print("CATCHED " + str(e))
        # session.callRemote(Pippo).addCallback(print_pippo_response).addErrback(lambda x: print("error"))
    else:
        print("NO CONNECTIONS AVAILABLE")


class Math(RPCProtocol):

    def __init__(self, session_manager):
        self.session_manager = session_manager
        super(Math, self).__init__()

    def connectionLost(self, reason):
        super().connectionLost(reason)
        print("- Removing connection due to " + str(reason))
        self.session_manager.remove(self)

    @Sum.responder
    def sum(self, a, b):
        total = a + b
        print('+ Did a sum: %d + %d = %d' % (a, b, total))
        return {'total': total}


def main():
    from twisted.internet import reactor
    from twisted.internet.protocol import Factory
    session_manager = SessionManager()

    def on_connection():
        session = Math(session_manager)
        session_manager.add(Client(session))
        return session

    math_factory = Factory()
    math_factory.protocol = on_connection

    endpoint = TCP6ServerEndpoint(reactor, 1234)
    endpoint.listen(math_factory)

    def execute():
        try:
            execute_pippo(session_manager.get_first_session())
        except:
            pass

    for i in range(1):
        timer_service = LoopingCall(execute)
        timer_service.start(10)  # Execute every 10 seconds

    print('started')
    reactor.run()


if __name__ == '__main__':
    main()
