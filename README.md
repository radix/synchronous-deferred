#SynchronousDeferred

## Abandoned

This code has never been used in production, and doesn't really approach the problem properly.

I strongly recommend checking out Effect, at https://github.com/python-effect/effect or https://pypi.python.org/pypi/effect/ instead.


## About


This is an alternative implementation of two classes:

 - twisted.internet.defer.Deferred
 - twisted.python.failure.Failure

These classes allow you to write a library that provides both asynchronous and synchronous
interfaces to your code.

They're not complete implementations of the entire interfaces, but they might become more thorough
once this code gets some serious use.

Is this code really necessary? Maybe not, if you decide to depend on Twisted anyway -- if you want
to provide a synchronous interface, maybe you can just use succeed() or fail() everywhere, and
have your uppermost synchronous API call some synchronize(d) function that requires the result
to be immediately available.
