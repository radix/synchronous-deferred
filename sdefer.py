import sys


class SynchronousDeferred(object):
    """
    An object which is similar to L{twisted.internet.defer.Deferred}, and
    allows a library author to easily include both synchronous and asynchronous
    interfaces.

    The notable differences between this class and C{Deferred} are thus:

      - There are no C{callback} or C{errback} methods on this class. You must
        provide the initial result to the constructor.
      - There is a L{synchronize} method, which returns or raises the current
        value.
      - There is no C{setTimeout} method, which is deprecated on the real
        C{Deferred} anyway.
      - There is no automatic logging of 'forgotten' failures, both to avoid
        depending on a particular logging framework and because if you are
        using this object, you should be calling C{synchronize} at the end,
        which will convert any leftover failures to a synchronous exception.

    The following are not implemented on this class mostly because they are
    very rarely used and I haven't gotten around to it:

      - C{chainDeferred}
      - C{pause}
      - C{unpause}

    """
    def __init__(self, result):
        """
        @param result: The result of this deferred.
        """
        self.result = result

    def synchronize(self):
        """
        Get the value of this result or raise an exception.

        This function should only be used at the uppermost level in an API,
        where it is absolutely certain that all lower-level operations have
        return values synchronously.
        """
        if isinstance(self.result, SynchronousFailure):
            self.result.raiseException()
        return self.result

    def _callCallback(self, callback, *args, **kwargs):
        try:
            self.result = callback(self.result, *args, **kwargs)
        except:
            self.result = SynchronousFailure()

    def addCallback(self, callback, *args, **kwargs):
        """
        Call C{callback} immediately with the current result if the current
        result is not a L{SynchronousFailure}. C{*args} and C{**kwargs} will
        also be passed.
        """
        if not isinstance(self.result, SynchronousFailure):
            self._callCallback(callback, *args, **kwargs)
        return self

    def addErrback(self, errback, *args, **kwargs):
        """
        Call C{errback} immediately with the current result if the current
        result is a L{SynchronousFailure}. C{*args} and C{**kwargs} will also
        be passed.
        """
        if isinstance(self.result, SynchronousFailure):
            self._callCallback(errback, *args, **kwargs)
        return self

    def addCallbacks(self, callback, errback,
                     callbackArgs=(), errbackArgs=(),
                     callbackKwargs={}, errbackKwargs={}):
        """
        Call C{callback} or C{errback}, depending on whether the current result
        is a failure. If C{callback} raises an exception, C{errback} will not
        be called.

        @param callbackArgs: The extra arguments to be passed to the callback.
        @param errbackArgs: The extra arguments to be passed to the errback.
        @param callbackKwargs: The extra keyword arguments to be passed to the
            callback.
        @param errbackKwargs: The extra keyword arguments to be passed to the
            errback.
        """
        if isinstance(self.result, SynchronousFailure):
            self._callCallback(errback, *errbackArgs, **errbackKwargs)
        else:
            self._callCallback(callback, *callbackArgs, **callbackKwargs)
        return self

    def addBoth(self, callback, *args, **kwargs):
        """
        Call the given C{callback} with the current value, no matter what the
        current value is.
        """
        self._callCallback(callback, *args, **kwargs)
        return self


class SynchronousFailure(Exception):
    """
    An object which supports a subset of the behavior that
    L{twisted.python.failure.Failure} provides.
    """
    def __init__(self, value=None):
        """
        @param value: The exception value to wrap. If none is specified,
            it will be inferred from the current exception state.
        """
        tb = None
        if value is None:
            info = sys.exc_info()
            value = info[1]
            tb = info[2]
        self.value = value
        self.tb = tb

    def check(self, *exceptionTypes):
        for exceptionType in exceptionTypes:
            if isinstance(self.value, exceptionType):
                return exceptionType

    def trap(self, *exceptionTypes):
        exceptionType = self.check(*exceptionTypes)
        if exceptionType is None:
            raise self
        return exceptionType

    def raiseException(self):
        raise type(self.value), self.value, self.tb
