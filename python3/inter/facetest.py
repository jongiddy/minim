import minter


class IFoo(minter.Face):

    """Foo blah blah"""

    x = """X blah blah"""

    def bar(q, r=None):
        """bar blah blah"""
        print(1)


class Foo:

    def __init__(self, x=None):
        self.x = x

    def bar(self, q, r=None):
        print(2)
        return q, r, self.x

    def foo(self):
        print(3)

    def __repr__(self):
        return "Foo(%s)" % self.x

IFoo.implementation(Foo)


f = Foo(3)

f.foo()
f.bar(4)

f1 = IFoo(f)
f1.bar(4)
f1.foo()
