
class InterfaceMetaclass(type):

    def __init__(interface, name, bases, dct):
        # Called when a new class is defined.  Use the dictionary of
        # declared attributes to create a mapping to the wrapped object
        type.__init__(interface, name, bases, {})
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
        interface.Provider = InterfaceProvider
        interface.attributes = [key for key in dct if not key.startswith('__')]

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
            # a wrapper object
            return type.__call__(interface, provider)
        if isinstance(provider, interface.Provider):
            # If the cast object provides this interface,
            for name in interface.attributes:
                getattr(provider, name)
            return type.__call__(interface, provider)
        raise TypeError(
            'Object {} does not support interface {}'. format(
                provider, interface.__name__))


class Interface(object, metaclass=InterfaceMetaclass):

    def __init__(self, provider):
        self.provider = provider

    def __getattribute__(self, name):
        my = super().__getattribute__
        if name in my('attributes'):
            return getattr(my('provider'), name)
        else:
            raise AttributeError(
                "{!r} interface has no attribute {!r}".format(
                    my('__class__').__name__, name))
