from twisted.internet.defer import Deferred, maybeDeferred


def deferWithTimeout(timeout, func=None, *args, **kwargs):
    """Call `func`, returning a `Deferred`.

    The `Deferred` will be cancelled after `timeout` seconds if not otherwise
    called.

    If `func` is not specified, or None, this will return a new
    :py:class:`Deferred` instance that will be cancelled after `timeout`
    seconds. Do not specify `args` or `kwargs` if `func` is `None`.

    :param timeout: The number of seconds before cancelling `d`.
    :param func: A callable, or `None`.
    :param args: Positional arguments to pass to `func`.
    :param kwargs: Keyword arguments to pass to `func`.
    """
    if func is None and len(args) == len(kwargs) == 0:
        d = Deferred()
    else:
        d = maybeDeferred(func, *args, **kwargs)

    from twisted.internet import reactor

    timeoutCall = reactor.callLater(timeout, d.cancel)

    def done(result):
        if timeoutCall.active():
            timeoutCall.cancel()
        return result

    return d.addBoth(done)
