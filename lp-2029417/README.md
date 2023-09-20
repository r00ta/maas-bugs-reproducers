# Reproducer for LP-2029417

## The bug

[Launchpad link](https://bugs.launchpad.net/maas/+bug/2029417)

Original stacktrace: 

```text
2023-09-13 21:46:35 -: [critical] Amp server or network failure unhandled by client application.  Dropping connection!  To avoid, add errbacks to ALL remote commands!
	Traceback (most recent call last):
	  File "/usr/lib/python3/dist-packages/twisted/internet/asyncioreactor.py", line 267, in run
	    self._asyncioEventloop.run_forever()
	  File "/usr/lib/python3/dist-packages/twisted/internet/asyncioreactor.py", line 290, in run
	    f(*args, **kwargs)
	  File "/usr/lib/python3/dist-packages/twisted/internet/defer.py", line 460, in callback
	    self._startRunCallbacks(result)
	  File "/usr/lib/python3/dist-packages/twisted/internet/defer.py", line 568, in _startRunCallbacks
	    self._runCallbacks()
	--- <exception caught here> ---
	  File "/usr/lib/python3/dist-packages/twisted/internet/defer.py", line 654, in _runCallbacks
	    current.result = callback(current.result, *args, **kw)
	  File "/usr/lib/python3/dist-packages/provisioningserver/rpc/common.py", line 312, in _safeEmit
	    return super()._safeEmit(box)
	  File "/usr/lib/python3/dist-packages/twisted/protocols/amp.py", line 1078, in _safeEmit
	    aBox._sendTo(self.boxSender)
	  File "/usr/lib/python3/dist-packages/twisted/protocols/amp.py", line 723, in _sendTo
	    proto.sendBox(self)
	  File "/usr/lib/python3/dist-packages/twisted/protocols/amp.py", line 2386, in sendBox
	    self.transport.write(box.serialize())
	  File "/usr/lib/python3/dist-packages/twisted/internet/_newtls.py", line 191, in write
	    FileDescriptor.write(self, bytes)
	  File "/usr/lib/python3/dist-packages/twisted/internet/abstract.py", line 356, in write
	    self.startWriting()
	  File "/usr/lib/python3/dist-packages/twisted/internet/abstract.py", line 443, in startWriting
	    self.reactor.addWriter(self)
	  File "/usr/lib/python3/dist-packages/twisted/internet/asyncioreactor.py", line 173, in addWriter
	    self._asyncioEventloop.add_writer(fd, callWithLogger, writer,
	  File "uvloop/loop.pyx", line 2399, in uvloop.loop.Loop.add_writer
	    
	  File "uvloop/loop.pyx", line 808, in uvloop.loop.Loop._add_writer
	    
	  File "uvloop/handles/poll.pyx", line 122, in uvloop.loop.UVPoll.start_writing
	    
	  File "uvloop/handles/poll.pyx", line 39, in uvloop.loop.UVPoll._poll_start
	    
	  File "uvloop/handles/handle.pyx", line 159, in uvloop.loop.UVHandle._ensure_alive
	    
	builtins.RuntimeError: unable to perform operation on <UVPoll closed=True 0x7f47e5f24120>; the handler is closed
	
2023-09-13 21:46:35 provisioningserver.rpc.common: [info] The handler is closed and the exception was unhandled. The connection is dropped.
```

Twisted `unhandledError` is calling `self.transport.loseConnection()` but `connectionLost` is not being called when the exception is raised from 
```
          File "/usr/lib/python3/dist-packages/twisted/internet/asyncioreactor.py", line 173, in addWriter
            self._asyncioEventloop.add_writer(fd, callWithLogger, writer,
```

## How to reproduce

Setup virtualenv

```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
``` 

patch `venv/lib/python3.10/site-packages/twisted/internet/abstract.py` so to simulate the exception to be raised
```bash
cp patches/abstract.py venv/lib/python3.10/site-packages/twisted/internet/abstract.py
```

Start the server
```bash
export IS_SERVER=yes
python server.py`
```

On another terminal, activate the venv and start the client
```bash
source venv/bin/activate
python client.py
```

In the server, reply `y` when you get the prompt

```text
Do you want asyncioreactor to raise builtins.RuntimeError? (y/n) y
```

As you can see the `unhandledError` is called and `transport.lostConnection()` is called as well. However, we don't get 
`connectionLost` called and we don't remove the connection from the pool. If the same exception is raised in the upper calls 
(like in `protocols/amp.py`) the connection is properly dropped.

```bash
$ python server.py 
Event loop implementation: <class 'uvloop.EventLoopPolicy'>
NO CONNECTIONS AVAILABLE
started
+ Did a sum: 10 + 20 = 30
Do you want asyncioreactor to raise builtins.RuntimeError? (y/n) y
+ raising builtins.RuntimeError
There is an unhandledError, let's see.
Amp server or network failure unhandled by client application.  Dropping connection!  To avoid, add errbacks to ALL remote commands!
Traceback (most recent call last):
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1030, in ampBoxReceived
    self._commandReceived(box)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1010, in _commandReceived
    deferred.addCallback(self._safeEmit)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 645, in addCallback
    return self.addCallbacks(callback, callbackArgs=args, callbackKeywords=kwargs)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 558, in addCallbacks
    self._runCallbacks()
--- <exception caught here> ---
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 1101, in _runCallbacks
    current.result = callback(  # type: ignore[misc]
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1040, in _safeEmit
    aBox._sendTo(self.boxSender)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 698, in _sendTo
    proto.sendBox(self)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 2336, in sendBox
    self.transport.write(box.serialize())
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 364, in write
    self.startWriting()
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 463, in startWriting
    raise builtins.RuntimeError("the handler is closed")
builtins.RuntimeError: the handler is closed

XXX It's not the first time an exception is raised. You should not be here as the connection should have been dropped!
+ raising builtins.RuntimeError
Unhandled error in Deferred:

Traceback (most recent call last):
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1030, in ampBoxReceived
    self._commandReceived(box)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1011, in _commandReceived
    deferred.addErrback(self.unhandledError)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 681, in addErrback
    return self.addCallbacks(
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 558, in addCallbacks
    self._runCallbacks()
--- <exception caught here> ---
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 1101, in _runCallbacks
    current.result = callback(  # type: ignore[misc]
  File "/tmp/maas-bugs-reproducers/lp-2029417/rpc.py", line 58, in unhandledError
    super().unhandledError(failure)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 2507, in unhandledError
    self.transport.loseConnection()
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 414, in loseConnection
    self.startWriting()
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 463, in startWriting
    raise builtins.RuntimeError("the handler is closed")
builtins.RuntimeError: the handler is closed

XXX It's not the first time an exception is raised. You should not be here as the connection should have been dropped!
+ raising builtins.RuntimeError
There is an unhandledError, let's see.
Amp server or network failure unhandled by client application.  Dropping connection!  To avoid, add errbacks to ALL remote commands!
Traceback (most recent call last):
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1030, in ampBoxReceived
    self._commandReceived(box)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1010, in _commandReceived
    deferred.addCallback(self._safeEmit)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 645, in addCallback
    return self.addCallbacks(callback, callbackArgs=args, callbackKeywords=kwargs)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 558, in addCallbacks
    self._runCallbacks()
--- <exception caught here> ---
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 1101, in _runCallbacks
    current.result = callback(  # type: ignore[misc]
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1040, in _safeEmit
    aBox._sendTo(self.boxSender)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 698, in _sendTo
    proto.sendBox(self)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 2336, in sendBox
    self.transport.write(box.serialize())
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 364, in write
    self.startWriting()
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 463, in startWriting
    raise builtins.RuntimeError("the handler is closed")
builtins.RuntimeError: the handler is closed

XXX It's not the first time an exception is raised. You should not be here as the connection should have been dropped!
+ raising builtins.RuntimeError
Unhandled error in Deferred:

Traceback (most recent call last):
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1030, in ampBoxReceived
    self._commandReceived(box)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1011, in _commandReceived
    deferred.addErrback(self.unhandledError)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 681, in addErrback
    return self.addCallbacks(
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 558, in addCallbacks
    self._runCallbacks()
--- <exception caught here> ---
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 1101, in _runCallbacks
    current.result = callback(  # type: ignore[misc]
  File "/tmp/maas-bugs-reproducers/lp-2029417/rpc.py", line 58, in unhandledError
    super().unhandledError(failure)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 2507, in unhandledError
    self.transport.loseConnection()
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 414, in loseConnection
    self.startWriting()
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 463, in startWriting
    raise builtins.RuntimeError("the handler is closed")
builtins.RuntimeError: the handler is closed

XXX It's not the first time an exception is raised. You should not be here as the connection should have been dropped!
+ raising builtins.RuntimeError
There is an unhandledError, let's see.
Amp server or network failure unhandled by client application.  Dropping connection!  To avoid, add errbacks to ALL remote commands!
Traceback (most recent call last):
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1030, in ampBoxReceived
    self._commandReceived(box)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1010, in _commandReceived
    deferred.addCallback(self._safeEmit)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 645, in addCallback
    return self.addCallbacks(callback, callbackArgs=args, callbackKeywords=kwargs)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 558, in addCallbacks
    self._runCallbacks()
--- <exception caught here> ---
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 1101, in _runCallbacks
    current.result = callback(  # type: ignore[misc]
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1040, in _safeEmit
    aBox._sendTo(self.boxSender)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 698, in _sendTo
    proto.sendBox(self)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 2336, in sendBox
    self.transport.write(box.serialize())
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 364, in write
    self.startWriting()
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 463, in startWriting
    raise builtins.RuntimeError("the handler is closed")
builtins.RuntimeError: the handler is closed

XXX It's not the first time an exception is raised. You should not be here as the connection should have been dropped!
+ raising builtins.RuntimeError
Unhandled error in Deferred:

Traceback (most recent call last):
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1030, in ampBoxReceived
    self._commandReceived(box)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1011, in _commandReceived
    deferred.addErrback(self.unhandledError)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 681, in addErrback
    return self.addCallbacks(
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 558, in addCallbacks
    self._runCallbacks()
--- <exception caught here> ---
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 1101, in _runCallbacks
    current.result = callback(  # type: ignore[misc]
  File "/tmp/maas-bugs-reproducers/lp-2029417/rpc.py", line 58, in unhandledError
    super().unhandledError(failure)
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 2507, in unhandledError
    self.transport.loseConnection()
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 414, in loseConnection
    self.startWriting()
  File "/tmp/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/abstract.py", line 463, in startWriting
    raise builtins.RuntimeError("the handler is closed")
builtins.RuntimeError: the handler is closed

+ There are 1 sessions
+ calling Pippo RPC procedure
XXX It's not the first time an exception is raised. You should not be here as the connection should have been dropped!
+ raising builtins.RuntimeError
+ There are 1 sessions
+ calling Pippo RPC procedure
XXX It's not the first time an exception is raised. You should not be here as the connection should have been dropped!
+ raising builtins.RuntimeError
```
