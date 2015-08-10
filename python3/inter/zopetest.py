import zope.interface


class IFoo(zope.interface.Interface):

    """Foo blah blah"""

    x = zope.interface.Attribute("""X blah blah""")

    def bar(q, r=None):
        """bar blah blah"""
        print(1)


class Foo:
    zope.interface.implements(IFoo)

    def __init__(self, x=None):
        self.x = x

    def bar(self, q, r=None):
        print(2)
        return q, r, self.x

    def foo(self):
        print(3)

    def __repr__(self):
        return "Foo(%s)" % self.x


f = Foo(3)

f.foo()
f.bar(4)

f1 = IFoo(f)
f1.bar(4)
f1.foo()
