import unittest

from jute import Interface, Dynamic, InterfaceConformanceError


# Simple interface hierarchy for testing

class Foo(Interface):
    foo = 99


class FooBar(Foo):

    def bar(self):
        """The bar method."""


class FooBaz(Foo):

    def baz(self):
        """The baz method."""


class IncompleteProviderTestsMixin:

    # Change this to the class to be tested
    HasBarOnly = object

    def test_incomplete_provider_validate_none(self):
        """Incomplete implementations are caught (during debugging).

        If an object claims to provide an interface, but doesn't,
        conversion to the interface will raise an
        InterfaceConformanceError in non-optimised code.

        In optimised code, the relatively expensive verification is
        removed and claims to implement an interface are always
        accepted. Accessing a non-interface attribute will still lead to
        an AttributeError, but this may occur later, when it is more
        difficult to diagnose where the invalid object came from.
        """
        obj = self.HasBarOnly()
        if __debug__:
            with self.assertRaises(InterfaceConformanceError):
                FooBar(obj)
        else:
            foobar = FooBar(obj)
            with self.assertRaises(AttributeError):
                foobar.foo

    def test_incomplete_provider_validate_true(self):
        """validate is True -> always raise InterfaceConformanceError."""
        obj = self.HasBarOnly()
        with self.assertRaises(InterfaceConformanceError):
            FooBar(obj, validate=True)

    def test_incomplete_provider_validate_false(self):
        """validate is False -> always raise late AttributeError."""
        obj = self.HasBarOnly()
        foobar = FooBar(obj, validate=False)
        with self.assertRaises(AttributeError):
            foobar.foo


class CompleteProviderTestsMixin:

    # Change this to the class to be tested
    HasFooBarBaz = object

    def test_provide(self):
        """An interface only has attributes defined in the interface (or
        in super-interfaces)."""
        obj = self.HasFooBarBaz()
        foobar = FooBar(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        with self.assertRaises(AttributeError):
            foobar.baz()
        self.assertEqual(obj.foo, 2)

    def test_inherit(self):
        """An interface can be mapped to a super-interface."""
        obj = self.HasFooBarBaz()
        foobar = FooBar(obj)
        foo = Foo(foobar)
        self.assertEqual(foo.foo, 1)
        with self.assertRaises(AttributeError):
            foo.bar()
        self.assertEqual(obj.foo, 1)

    def test_upcast_fails(self):
        """An interface cannot be mapped to a sub-interface, even if the
        wrapped instance could be."""
        obj = self.HasFooBarBaz()
        foo = Foo(obj)
        with self.assertRaises(TypeError):
            FooBar(foo)

    def test_duck_fails(self):
        """Duck-typed object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails with a
        TypeError."""
        obj = self.HasFooBarBaz()
        with self.assertRaises(TypeError):
            FooBaz(obj)

    def test_wrapped_duck_fails(self):
        """Duck-typed wrapped object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails with a
        TypeError."""
        obj = self.HasFooBarBaz()
        foobar = FooBar(obj)
        with self.assertRaises(TypeError):
            FooBaz(foobar)

    def test_subclass_provider_provides_interface(self):
        """Subclassing an implementation and a provider works."""
        class FooBarBazSubclass(self.HasFooBarBaz, FooBaz.Provider):
            pass
        obj = FooBarBazSubclass()
        foobar = FooBar(obj)
        foobaz = FooBaz(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        foobaz.baz()
        self.assertEqual(obj.foo, 3)

    def test_provider_subclass_provides_interface(self):
        """Subclassing a provider and an implementation works."""
        class FooBarBazSubclass(FooBaz.Provider, self.HasFooBarBaz):
            pass
        obj = FooBarBazSubclass()
        foobar = FooBar(obj)
        foobaz = FooBaz(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        foobaz.baz()
        self.assertEqual(obj.foo, 3)


class FooBarBaz(FooBar.Provider):

    """FooBar provider class.

    A class which implements FooBar, and looks like FooBaz, but does
    not implement FooBaz.
    """

    foo = 1

    def bar(self):
        self.foo = 2

    def baz(self):
        self.foo = 3


class IncompleteFooBar(FooBar.Provider):
    # doesn't implement foo

    def bar():
        pass


class InterfaceProviderTests(
        CompleteProviderTestsMixin, IncompleteProviderTestsMixin,
        unittest.TestCase):

    HasFooBarBaz = FooBarBaz
    HasBarOnly = IncompleteFooBar


class FooBarBazDynamic(Dynamic.Provider):

    def provides_interface(self, interface):
        return interface.implemented_by(FooBar)

    _foo = 1

    def bar(self):
        self._foo = 2

    def baz(self):
        self._foo = 3

    def __getattr__(self, name):
        if name == 'foo':
            return self._foo
        return super().__getattr__(name)


class IncompleteFooBarDynamic(Dynamic.Provider):
    # doesn't implement foo

    def provides_interface(self, interface):
        return interface.implemented_by(FooBar)

    def bar():
        pass


class DynamicProviderTests(
        CompleteProviderTestsMixin, IncompleteProviderTestsMixin,
        unittest.TestCase):

    HasFooBarBaz = FooBarBazDynamic
    HasBarOnly = IncompleteFooBarDynamic

    def test_subclass_provides_interface(self):
        class FooBarBazSubclass(self.HasFooBarBaz):

            def provides_interface(self, interface):
                return (
                    interface.implemented_by(FooBar) or
                    interface.implemented_by(FooBaz)
                )

        obj = FooBarBazSubclass()
        foobar = FooBar(obj)
        foobaz = FooBaz(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        foobaz.baz()
        self.assertEqual(obj.foo, 3)


class RegisteredFooBarBaz:

    """FooBar provider class.

    A class which implements FooBar, and looks like FooBaz, but does
    not implement FooBaz.
    """

    foo = 1

    def bar(self):
        self.foo = 2

    def baz(self):
        self.foo = 3

FooBar.register_implementation(RegisteredFooBarBaz)


class RegisteredIncompleteFooBar:
    # doesn't implement foo

    foo = 1

    def bar():
        pass

# Needs to be complete for registration, but then remove part of class.
# Document non-deletion of interface attributes as a requirement for
# registration.
FooBar.register_implementation(RegisteredIncompleteFooBar)
del RegisteredIncompleteFooBar.foo


class Capitalizable(Interface):

    """An interface provided by string type."""

    def capitalize(self):
        """Return first character capitalized and rest lowercased."""


class RegisteredImplementationTests(
        CompleteProviderTestsMixin, unittest.TestCase):

    HasFooBarBaz = RegisteredFooBarBaz

    def test_builtin_type(self):
        """Built in types can be registered."""
        Capitalizable.register_implementation(str)
        c = Capitalizable('a stRing')
        self.assertEqual(c.capitalize(), 'A string')

    def test_incomplete_implementation_cannot_be_registered(self):
        with self.assertRaises(InterfaceConformanceError):
            FooBar.register_implementation(IncompleteFooBar)

    def test_incomplete_provider_validate_none(self):
        """Incomplete implementations are caught (during debugging).

        If a class successfully registers an interface, but doesn't
        provide the interface (e.g. deletes an attribute), the problem
        is not detected during creation.  A normal attribute error will
        be raised when the attributes is accessed.

        Note, this is the same as `validate=False` for non-registered
        providers, indicating that classes verified before instantiation
        are not verified when being instantiated.
        """
        obj = RegisteredIncompleteFooBar()
        foobar = FooBar(obj)
        with self.assertRaises(AttributeError):
            foobar.foo

    def test_incomplete_provider_validate_true(self):
        """validate is True -> always raise InterfaceConformanceError."""
        obj = RegisteredIncompleteFooBar()
        with self.assertRaises(InterfaceConformanceError):
            FooBar(obj, validate=True)

    def test_incomplete_provider_validate_false(self):
        """validate is False -> always raise late AttributeError."""
        obj = RegisteredIncompleteFooBar()
        foobar = FooBar(obj, validate=False)
        with self.assertRaises(AttributeError):
            foobar.foo

    def test_non_class_fails(self):
        """A non-class interface provider cannot be registered.

        This is required to ensure that registered implementations can
        be tested quickly using `issubclass`"""
        with self.assertRaises(TypeError):
            Capitalizable.register_implementation('')


class FooBarBazSubclass(FooBar):
    pass


class DoubleInheritedInterfaceTests(unittest.TestCase):

    """Check that all base classes are treated as provided by an interface.

    If we mistakenly just use the first level of base classes, these tests
    should fail.
    """

    def test_provider(self):
        class FBBImpl(FooBarBazSubclass.Provider):
            foo = 1
            bar = 2

        fbb = FBBImpl()
        self.assertTrue(Foo.provided_by(fbb))

    def test_registered(self):
        class FBBImpl:
            foo = 1
            bar = 2

        FooBarBazSubclass.register_implementation(FBBImpl)

        fbb = FBBImpl()
        self.assertTrue(Foo.provided_by(fbb))


class ImplementedByTests(unittest.TestCase):

    def test_implemented_by_self(self):
        """An interface is implemented by itself."""
        self.assertTrue(Foo.implemented_by(Foo))

    def test_implemented_by_subinterface(self):
        """An interface is implemented by a sub-interface."""
        self.assertTrue(Foo.implemented_by(FooBar))

    def test_implemented_by_registered_class(self):
        """An interface is implemented by a registered class."""
        self.assertTrue(Foo.implemented_by(RegisteredFooBarBaz))

    def test_implemented_by_verifiable_provider_class(self):
        """An interface is implemented by a provider class if verified."""
        class ProviderClass(Foo.Provider):
            foo = 1
        self.assertTrue(Foo.implemented_by(ProviderClass))

    def test_implemented_by_non_verifiable_provider_class(self):
        """An interface is implemented by non-verified provider class."""
        class ProviderClass(Foo.Provider):
            # Instance is a valid provider, but the class itself is not.

            def __init__(self):
                self.foo = 1
        self.assertTrue(Foo.implemented_by(ProviderClass))

    def test_not_implemented_by_provider_instance(self):
        """An interface is not implemented by a provider instance."""
        self.assertFalse(Foo.implemented_by(FooBarBaz()))

    def test_not_implemented_by_registered_instance(self):
        """An interface is not implemented by a registered class instance."""
        self.assertFalse(Foo.implemented_by(RegisteredFooBarBaz()))

    def test_not_implemented_by_non_provider(self):
        """An interface is not implemented by a non-providing class."""
        class C:
            foo = 1
        self.assertFalse(Foo.implemented_by(C))
