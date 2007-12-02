import sys
import traceback

from sdefer import SynchronousDeferred, SynchronousFailure

from unittest import TestCase


class SynchronousDeferredTests(TestCase):
    """
    Tests for L{SynchronousDeferred}.
    """
    def test_basicSynchronize(self):
        """
        The C{synchronize} method returns the current value.
        """
        self.assertEquals(SynchronousDeferred(None).synchronize(), None)
        self.assertEquals(SynchronousDeferred("foo").synchronize(), "foo")

    def test_synchronizeFailure(self):
        """
        If the value of a deferred is a failure, it should be raised instead of
        returned.
        """
        deferred = SynchronousDeferred(SynchronousFailure(RuntimeError()))
        self.assertRaises(RuntimeError, deferred.synchronize)

    def test_addCallback(self):
        """
        C{addCallback} calls the callback passed immediately and returns itself.
        """
        l = []
        sd = SynchronousDeferred(None)
        self.assertEquals(sd.addCallback(l.append), sd)
        self.assertEquals(l, [None])

    def test_addCallbackExtraArguments(self):
        """
        C{addCallback} passes extra arguments to the callback.
        """
        l = []
        def cb(r, extra, more=None):
            l.append((r, extra, more))

        SynchronousDeferred("foo").addCallback(cb, 1, more="heyo")
        self.assertEquals(l, [("foo", 1, "heyo")])

    def test_callbackResultChangesValue(self):
        """
        The result of a callback affects the result returned from
        C{synchronize}.
        """
        sd = SynchronousDeferred("foo")
        sd.addCallback(lambda r: 42)
        self.assertEquals(sd.synchronize(), 42)

    def test_callbackResultChangesNextCallbackArgument(self):
        """
        The result of a callback affects the argument passed to the next
        callback.
        """
        sd = SynchronousDeferred("foo")
        sd.addCallback(lambda r: 42)
        l = []
        sd.addCallback(l.append)
        self.assertEquals(l, [42])

    def test_addErrback(self):
        """
        C{addErrback} immediately calls the errback when the current result is
        a failure.
        """
        failure = SynchronousFailure(RuntimeError())
        sd = SynchronousDeferred(failure)
        l = []
        self.assertEquals(sd.addErrback(l.append), sd)
        self.assertEquals(l, [failure])

    def test_addCallbackOnlyCalledOnSuccess(self):
        """
        C{addCallback} will not call its argument when the current value is not
        a success.
        """
        l = []
        SynchronousDeferred(
            SynchronousFailure(RuntimeError())).addCallback(l.append)
        self.assertEquals(l, [])

    def test_addErrbackOnlyCalledOnFailure(self):
        """
        C{addErrback} will not call its argument when the current value is not
        an error.
        """
        l = []
        SynchronousDeferred("foo").addErrback(l.append)
        self.assertEquals(l, [])

    def test_addErrbackExtraArguments(self):
        """
        C{addErrback} passes extra arguments to the callback.
        """
        l = []
        def eb(r, extra, more=None):
            l.append((r, extra, more))

        failure = SynchronousFailure(RuntimeError())
        SynchronousDeferred(failure).addErrback(eb, 1, more="heyo")
        self.assertEquals(l, [(failure, 1, "heyo")])

    def test_errbackResultChangesValue(self):
        """
        The result of an errback affects the result returned from
        C{synchronize}.
        """
        sd = SynchronousDeferred(SynchronousFailure(RuntimeError()))
        sd.addErrback(lambda r: 42)
        self.assertEquals(sd.synchronize(), 42)

    def test_errbackResultChangesNextCallbackArgument(self):
        """
        The result of an errback affects the argument passed to the next
        callback.
        """
        sd = SynchronousDeferred(SynchronousFailure(RuntimeError()))
        sd.addErrback(lambda r: 42)
        l = []
        sd.addCallback(l.append)
        self.assertEquals(l, [42])

    def test_errorRaisingCallback(self):
        """
        If a callback raises an exception, errbacks will be called.
        """
        sd = SynchronousDeferred("foo")
        def callback(ignored):
            1/0
        sd.addCallback(callback)
        l = []
        sd.addErrback(l.append)
        self.assertEquals(len(l), 1)
        self.assertTrue(l[0].check(ZeroDivisionError))

    def test_errorRaisingErrback(self):
        """
        If an errback raises an exception, errbacks will be called.
        """
        sd = SynchronousDeferred(SynchronousFailure(RuntimeError()))
        def errback(ignored):
            1/0
        sd.addErrback(errback)
        l = []
        sd.addErrback(l.append)
        self.assertEquals(len(l), 1)
        self.assertTrue(l[0].check(ZeroDivisionError))

    def test_addCallbacksCallsCallback(self):
        """
        C{addCallbacks} calls the callback passed to it, and not the errback,
        if the current result is a success.
        """
        sd = SynchronousDeferred("foo")
        successes = []
        failures = []
        self.assertEquals(sd.addCallbacks(successes.append, failures.append),
                          sd)
        self.assertEquals(successes, ["foo"])
        self.assertEquals(failures, [])

    def test_addCallbacksCallsErrback(self):
        """
        C{addCallbacks} calls the errback passed to it, and not the callback,
        if the current result is a failure.
        """
        failure = SynchronousFailure(RuntimeError())
        sd = SynchronousDeferred(failure)
        successes = []
        failures = []
        sd.addCallbacks(successes.append, failures.append)
        self.assertEquals(successes, [])
        self.assertEquals(failures, [failure])

    def test_addCallbacksOnlyCallsOne(self):
        """
        If the callback raises an exception, the errback won't be called.
        """
        sd = SynchronousDeferred("foo")
        failures = []
        sd.addCallbacks(lambda r: 1/0, failures.append)
        self.assertEquals(failures, [])

    def test_addCallbacksExtraArgumentsOnCallback(self):
        """
        addCallbacks takes some extra arguments to pass to its callback.
        """
        sd = SynchronousDeferred("foo")
        l = []
        def cb(r, extra, more=None):
            l.append((r, extra, more))
        sd.addCallbacks(cb, lambda ignored: None,
                        (1,), {},
                        {"more": "heyo"}, {})
        self.assertEquals(l, [("foo", 1, "heyo")])

    def test_addCallbacksExtraArgumentsOnErrback(self):
        """
        addCallbacks takes some extra arguments to pass to its errback.
        """
        failure = SynchronousFailure(RuntimeError())
        sd = SynchronousDeferred(failure)
        l = []
        def eb(r, extra, more=None):
            l.append((r, extra, more))
        sd.addCallbacks(lambda ignored: None, eb,
                        (), (1,),
                        {}, {"more": "heyo"})
        self.assertEquals(l, [(failure, 1, "heyo")])

    def test_addBothSuccess(self):
        """
        addBoth adds a callback to be run on success.
        """
        l = []
        sd = SynchronousDeferred("foo").addBoth(l.append)
        self.assertEquals(l, ["foo"])

    def test_addBothSuccessExtraArgs(self):
        """
        addBoth takes extra arguments, and they get passed in the success case.
        """
        sd = SynchronousDeferred("foo")
        l = []
        def cb(r, extra, more=None):
            l.append((r, extra, more))
        sd.addBoth(cb, 1, more="heyo")
        self.assertEquals(l, [("foo", 1, "heyo")])

    def test_addBothFailure(self):
        """
        addBoth calls a callback on failure.
        """
        failure = SynchronousFailure(RuntimeError())
        l = []
        sd = SynchronousDeferred(failure).addBoth(l.append)
        self.assertEquals(l, [failure])

    def test_addBothFailureExctraArgs(self):
        """
        addBoth adds a callback to be run on success.
        """
        failure = SynchronousFailure(RuntimeError())
        sd = SynchronousDeferred(failure)
        l = []
        def eb(r, extra, more=None):
            l.append((r, extra, more))
        sd.addBoth(eb, 1, more="heyo")
        self.assertEquals(l, [(failure, 1, "heyo")])



class SynchronousFailureTests(TestCase):
    """
    Tests for L{SynchronousFailure}.
    """

    def test_passInException(self):
        """
        SynchronousFailure takes an Exception instance as its parameter.
        """
        failure = SynchronousFailure(RuntimeError("hello"))
        self.assertTrue(failure.check(RuntimeError))

    def test_getExceptionFromEnvironment(self):
        """
        SynchronousFailure infers the current exception and traceback from the
        environment.
        """
        try:
            1/0
        except:
            failure = SynchronousFailure()
        self.assertTrue(failure.check(ZeroDivisionError))

    def test_check(self):
        """
        Check accepts multiple exception types, and returns the exception type
        which matched.
        """
        failure = SynchronousFailure(RuntimeError())
        self.assertEquals(failure.check(ZeroDivisionError, RuntimeError),
                          RuntimeError)

    def test_trapReturns(self):
        """
        The C{trap} method is like C{check} in that it returns the passed
        exception type that matches the failure's value.
        """
        failure = SynchronousFailure(RuntimeError())
        self.assertEquals(failure.trap(ZeroDivisionError, RuntimeError),
                          RuntimeError)

    def test_trapRaises(self):
        """
        If the exception types passed to C{trap} do not match the failure's
        value, the failure itself is raised. Yes, that's weird.
        """
        failure = SynchronousFailure(RuntimeError())
        self.assertRaises(SynchronousFailure, failure.trap, ZeroDivisionError)

    def test_raiseException(self):
        """
        C{raiseException} raises the original exception, including traceback.
        """
        try:
            1/0
        except:
            failure = SynchronousFailure()

        try:
            failure.raiseException()
        except ZeroDivisionError, e:
            tb = traceback.extract_tb(sys.exc_info()[2])
            innerline = tb[-1][-1]
        except Exception, e:
            self.fail("raiseException raised the wrong exception: %s" % (e,))
        else:
            self.fail("raiseException didn't raise an exception.")

        self.assertEquals(innerline, '1/0')
