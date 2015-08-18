"""
Interfaces for Python.

Yet another interface module for Python.

Although duck typing is generally considered the Pythonic way of dealing
with object compatibility, it's major problem is that it relies on
syntactical compatibility to indicate semantic compatibility.
Interfaces provide a way to indicate semantic compatibility
directly.

Most existing interface modules for Python (e.g. ``abc``,
and ``zope.interface``) check that implementing classes provide all the
attributes specified in the interface.  But they ignore the other side
of the contract, failing to ensure that the receiver of the interface
only calls operations specified in the interface.  This module checks
both, ensuring that called code will work with any provider of the
interface, not just the one with which it was tested.

Interfaces have minimal impact on the implementing classes.  Although
implementing classes must subclass an InterfaceProvider class, that
class is completely empty, adding no additional attributes or
metaclasses to the implementing class.

The interface hierarchy and the implementer hierarchy are completely
distinct, so you don't get tied up in knots getting a sub-class to
implement a sub-interface when the super-class already implements the
super-interface.

To prevent interface checks from affecting performance, we recommend
to code interface conversions inside ``if __debug__:`` clauses. This
can be used to allow interface checks during debugging, and production
code to use the original objects by running Python with the ``-O`` flag.

:Example:

>>> import sys
>>> from inter import Interface
>>> class Writes(Interface):
...     def write(self, buf):
...         "Write the string buf."
...
>>> class StdoutWriter(Writes.Provider):
...     def flush(self):
...         sys.stdout.flush()
...     def write(self, buf):
...         sys.stdout.write(buf)
...
>>> def output(writer, buf):
...     if __debug__:
...         writer = Writes(writer)
...     writer.write(buf)
...     writer.flush()
...
>>> out = StdoutWriter()
>>> output(out, 'Hello, World!')

In normal Python mode, ``writer`` will be replaced by the interface,
and the attempt to use ``flush``, which is not part of the interface,
will fail.

In optimised Python, ``writer`` will use the original object, failing to
see the error (which has hopefully been fixed by now), but running
faster without the intervening interface replacement.

Note, there is no way to specify non-subclassed types as implementing an
interface.  Hence, ``sys.stdout`` cannot be indicated as satisfying the
``Writes`` interface.
"""


class InterfaceMetaclass(type):

    KEPT = frozenset((
        '__module__', '__qualname__',
        '__init__', '__del__',
        '__getattribute__',
    ))

    def __new__(meta, name, bases, dct):
        # Called when a new class is defined.  Use the dictionary of
        # declared attributes to create a mapping to the wrapped object
        BaseInterfaceProviders = []
        for base in bases:
            if base is not object and issubclass(base, Interface):
                # base class is a super-interface of this interface
                BaseInterfaceProviders.append(base.Provider)

        class InterfaceProvider(*BaseInterfaceProviders):
            # Subclassing this class indicates that the class implements
            # the interface.  Since this class inherits the provider
            # classes of super-interfaces, it also indicates that the
            # class implements those interfaces as well.
            pass
        instance_attributes = {}
        object_attributes = set()
        for key, value in dct.items():
            # Almost all attributes on the interface are mapped to
            # return the equivalent attributes on the wrapped object.
            if key in meta.KEPT:
                # A few attributes need to be kept pointing to the
                # interface object.
                instance_attributes[key] = value
            elif key.startswith('__'):
                # Special methods, e.g. __iter__, can be called
                # directly on an instance without going through
                # __getattribute__.  For example, `for i in x:` will
                # call x.__iter__() without resolving the name in the
                # usual way.  Hence, we need to create these functions
                # directly on the class.
                def create_proxy_function(name):
                    # Creating the function inside another function
                    # creates a closure in which `name` stays set to its
                    # current value, for use inside the inner function.
                    def proxy_function(self, *args, **kw):
                        my = object.__getattribute__
                        method = getattr(my(self, 'provider'), name)
                        return method(*args, **kw)
                    return proxy_function
                instance_attributes[key] = create_proxy_function(key)
                # Also add the name to `instance_attributes` to ensure that
                # `__getattribute__` does not reject the name for the
                # cases where Python does go through the usual process,
                # e.g. x.__iter__
                object_attributes.add(key)
            else:
                # All other attributes are simply mapped using
                # `__getattribute__`.
                object_attributes.add(key)
        instance_attributes['Provider'] = InterfaceProvider
        instance_attributes['object_attributes'] = object_attributes
        interface = super().__new__(meta, name, bases, instance_attributes)
        return interface

    def __call__(interface, provider):
        # Calling Interface(object) will call this function first.  We
        # get a chance to return the same object if suitable.
        """Cast the object to this interface."""
        if provider.__class__ is interface:
            # If the cast object is this interface, just return
            # the same interface.
            return provider
        if isinstance(provider, interface):
            # If the cast object is a subclass of this face, create
            # a wrapper object.
            return super().__call__(provider)
        if isinstance(provider, interface.Provider):
            # If the cast object provides this interface, test that the
            # object has all required attributes and create a wrapper
            # object.
            for name in interface.object_attributes:
                getattr(provider, name)
            return super().__call__(provider)
        raise TypeError(
            'Object {} does not support interface {}'. format(
                provider, interface.__name__))


class Interface(object, metaclass=InterfaceMetaclass):

    def __init__(self, provider):
        """Wrap an object with an interface object."""
        self.provider = provider

    def __getattribute__(self, name):
        """
        Check and return an attribute for the interface.

        When an interface object has an attribute accessed, check that
        the attribute is specified by the interface, and then retrieve
        it from the wrapped object.
        """
        my = super().__getattribute__
        if name in my('object_attributes'):
            return getattr(my('provider'), name)
        else:
            raise AttributeError(
                "{!r} interface has no attribute {!r}".format(
                    my('__class__').__name__, name))
