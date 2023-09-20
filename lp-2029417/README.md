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

Twisted `unhandledError` is not being called if the exception comes from any point in the previous stacktrace. So, we are 
going to patch `amp.py` to raise it.

## How to reproduce

Setup virtualenv

```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
``` 

patch `venv/lib/python3.10/site-packages/twisted/internet/abstract.py` so to simulate the exception to be raised
```bash
cp patches/amp.py venv/lib/python3.10/site-packages/twisted/protocols/amp.py
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

As you can see the `unhandledError` is not being called in our case, so we definitely need to catch the exception as proposed 
in the comments in [models.py](models.py). 

```bash
$ python server.py 
Event loop implementation: <class 'uvloop.EventLoopPolicy'>
NO CONNECTIONS AVAILABLE
started
+ Did a sum: 10 + 20 = 30
+ There are 1 sessions
+ calling Pippo RPC procedure
Do you want asyncioreactor to raise builtins.RuntimeError? (y/n) y
+ raising builtins.RuntimeError
Unhandled error in Deferred:

Traceback (most recent call last):
  File "/home/r00ta/repos/maas-repos/maas-bugs-reproducers/lp-2029417/server.py", line 89, in execute
    execute_pippo(session_manager.get_first_session())
  File "/home/r00ta/repos/maas-repos/maas-bugs-reproducers/lp-2029417/server.py", line 42, in execute_pippo
    client(Pippo).addCallback(print_pippo_response)
  File "/home/r00ta/repos/maas-repos/maas-bugs-reproducers/lp-2029417/models.py", line 80, in __call__
    return deferWithTimeout(
  File "/home/r00ta/repos/maas-repos/maas-bugs-reproducers/lp-2029417/utils.py", line 22, in deferWithTimeout
    d = maybeDeferred(func, *args, **kwargs)
--- <exception caught here> ---
  File "/home/r00ta/repos/maas-repos/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/internet/defer.py", line 234, in maybeDeferred
    result = f(*args, **kwargs)
  File "/home/r00ta/repos/maas-repos/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 948, in callRemote
    return co._doCommand(self)
  File "/home/r00ta/repos/maas-repos/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 1963, in _doCommand
    d = proto._sendBoxCommand(
  File "/home/r00ta/repos/maas-repos/maas-bugs-reproducers/lp-2029417/rpc.py", line 37, in _sendBoxCommand
    return super()._sendBoxCommand(
  File "/home/r00ta/repos/maas-repos/maas-bugs-reproducers/lp-2029417/venv/lib/python3.10/site-packages/twisted/protocols/amp.py", line 879, in _sendBoxCommand
    raise builtins.RuntimeError("the handler is closed")
builtins.RuntimeError: the handler is closed


+ There are 1 sessions
+ calling Pippo RPC procedure
Do you want asyncioreactor to raise builtins.RuntimeError? (y/n)
```
