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
>>> from jute import Interface
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

In the above code, ``writer`` will be replaced by the interface, and the
attempt to use ``flush``, which is not part of the interface, will fail.

Subclassing an interface's Provider attribute indicates a claim to
implement the interface.  This claim is verified during conversion to
the interface, but only in non-optimised code.

In optimised Python, ``writer`` will use the original object, and should
run faster without the intervening interface replacement.  In this case,
the code will work with the current implementation, but may fail if a
different object, that does not support ``flush`` is passed.

Note, there is no way to specify non-subclassed types as implementing an
interface.  Hence, ``sys.stdout`` cannot be indicated as satisfying the
``Writes`` interface.
"""


class InterfaceConformanceError(Exception):

    """Object does not conform to interface specification.

    Exception indicating that an object claims to provide an interface,
    but does not match the interface specification.

    This is almost a TypeError, but an object provides two parts to its
    interface implementation: a claim to provide the interface, and the
    attributes that match the interface specification.  This exception
    indicates the partial match of claiming to provide the interface,
    but not actually providing all the attributes required by an
    interface.

    It could also be considered an AttributeError, as when validation is
    off, that is the alternative exception (that might be) raised.
    However, future versions of this module may perform additional
    validation to catch TypeError's (e.g. function paramete matching).

    It was also tempting to raise a NotImplementedError, which captures
    some of the meaning. However, NotImplementedError is usually used
    as a marker for abstract methods or in-progress partial
    implementations.  In particular, a developer of an interface
    provider class may use NotImplementedError to satisy the interface
    where they know the code does not use a particular attribute of the
    interface.  Using a different exception causes less confusion.
    """
    pass


# Declare the base classes for the `Interface` class here so the
# metaclass `__new__` method can avoid running
# `issubclass(base, Interface)` during the creation of the `Interface`
# class, at a time when the name `Interface` does not exist.
_InterfaceBaseClasses = (object,)


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
        class_attributes = {}
        provider_attributes = set()
        for base in bases:
            if (
                base not in _InterfaceBaseClasses and
                issubclass(base, Interface)
            ):
                # base class is a super-interface of this interface
                BaseInterfaceProviders.append(base.Provider)
                # This interface provides all attributes from the base
                # interface
                provider_attributes |= base.provider_attributes

        class InterfaceProvider(*BaseInterfaceProviders):
            # Subclassing this class indicates that the class implements
            # the interface.  Since this class inherits the provider
            # classes of super-interfaces, it also indicates that the
            # class implements those interfaces as well.
            pass
        for key, value in dct.items():
            # Almost all attributes on the interface are mapped to
            # return the equivalent attributes on the wrapped object.
            if key in meta.KEPT:
                # A few attributes need to be kept pointing to the
                # interface object.
                class_attributes[key] = value
            elif key.startswith('__'):
                # Special methods, e.g. __iter__, can be called
                # directly on an instance without going through
                # __getattribute__.  For example, `for i in x:` will
                # call `x.__iter__()` without resolving the name in the
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
                class_attributes[key] = create_proxy_function(key)
                # Also add the name to `provider_attributes` to ensure
                # that `__getattribute__` does not reject the name for
                # the cases where Python does go through the usual
                # process, e.g. a literal `x.__iter__`
                provider_attributes.add(key)
            else:
                # All other attributes are simply mapped using
                # `__getattribute__`.
                provider_attributes.add(key)
        class_attributes['Provider'] = InterfaceProvider
        class_attributes['provider_attributes'] = provider_attributes
        interface = super().__new__(meta, name, bases, class_attributes)
        return interface

    def __call__(interface, obj, validate=None):
        # Calling Interface(object) will call this function first.  We
        # get a chance to return the same object if suitable.
        """Cast the object to this interface."""
        if type(obj) is interface:
            # If the object to be cast is already an instance of this
            # interface, just return the same object.
            return obj
        interface.raise_if_not_provided_by(obj, validate)
        # create a wrapper object to enforce only this interface.
        return super().__call__(obj)

    def raise_if_not_provided_by(interface, obj, validate=None):
        """Check if object provides the interface.

        :raise: an informative error if not. For example, a
        non-implemented attribute is returned in the exception.
        """
        not_implemented = None
        if isinstance(obj, interface):
            # an object that has already been wrapped by an interface,
            # and that interface is a sub-class of this interface, so it
            # must support all operations
            pass
        elif (
            isinstance(obj, interface.Provider) or
            isinstance(obj, (Dynamic, Dynamic.Provider)) and
                obj.provides_interface(interface)
        ):
            # The object claims to provide the interface, either by
            # subclassing the interface's provider class, or by
            # implementing Dynamic and returning True from the provides
            # method.  Since it is just a claim, verify that the
            # attributes are supported.  If `validate` is False or is
            # not set and code is optimised, accept claims without
            # validating.
            if validate is None and __debug__ or validate:
                for name in interface.provider_attributes:
                    if not hasattr(obj, name):
                        if not_implemented is None:
                            not_implemented = []
                        not_implemented.append(repr(name))
                if not_implemented:
                    if len(not_implemented) == 1:
                        attribute = 'attribute'
                    else:
                        attribute = 'attributes'
                    raise InterfaceConformanceError(
                        'Object {} does not provide {} {}'.format(
                            obj, attribute, ', '.join(not_implemented)))
        else:
            raise TypeError(
                'Object {} does not provide interface {}'. format(
                    obj, interface.__name__))

    def provided_by(interface, obj):
        """Check if object claims to provide the interface.

        :return: True if interface is provided by the object, else False.
        """
        return (
            isinstance(obj, (interface, interface.Provider)) or
            isinstance(obj, (Dynamic, Dynamic.Provider)) and
                obj.provides_interface(interface)
            )


class Interface(*_InterfaceBaseClasses, metaclass=InterfaceMetaclass):

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
        if name in my('provider_attributes'):
            return getattr(my('provider'), name)
        else:
            raise AttributeError(
                "{!r} interface has no attribute {!r}".format(
                    my('__class__').__name__, name))


class Dynamic(Interface):

    """Interface to dynamically provide other interfaces."""

    def provides_interface(self, interface):
        """Check whether this instance provides an interface.

        This method returns True when the interface class is provided,
        or False when the interface is not provided.
        """
