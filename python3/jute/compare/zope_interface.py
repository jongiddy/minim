from time import time
import zope.interface


class Increments(zope.interface.Interface):

    def increment():
        """Increment something"""


class IncrementsBar(Increments):

    """Provide bar as an attribute"""

    bar = zope.interface.Attribute("""An attribute""")


@zope.interface.implementer(IncrementsBar)
class IncrementingInteger:

    """Increment an integer when increment is called."""

    bar = 2

    def increment(self):
        self.bar += 1


def f(incrementer):
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
