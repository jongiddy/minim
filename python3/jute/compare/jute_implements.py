from time import time
import jute

# Create an interface IFoo
# Create a sub-interface IFooBar
# Create a class FooBarBaz implementing IFooBar
# Repeatedly create an instance of FooBarBaz and pass it to a function
# that wants an IFoo
# Call foo
# Time all the above
# Create a single instance of FooBarBaz. Confirm whether a function
# wanting an IFoo succeeds or fails calling foo, bar, baz
# Check whether a Foo object (implementing only foo) can be passed to a
# function wanting an IFooBar, and if it can, whether it succeeds or
# fails calling foo, bar, baz


class Increments(jute.Interface):

    def increment():
        """Increment something"""


class IncrementsBar(Increments):

    """Provide bar as an attribute"""

    bar = 1


@jute.implements(IncrementsBar)
class IncrementingInteger:

    """Increment an integer when increment is called."""

    bar = 2

    def increment(self):
        self.bar += 1


def f(incrementer):
    if __debug__:
        incrementer = Increments(incrementer)
    incrementer.increment()


def test_time():
    start = time()
    for i in range(1000000):
        inc = IncrementingInteger()
        f(inc)
    stop = time()
    print(stop - start)


def test_time1():
    start = time()
    inc = IncrementingInteger()
    for i in range(1000000):
        f(inc)
    stop = time()
    print(stop - start)


def main():
    test_time()
    test_time1()

if __name__ == '__main__':
    main()
