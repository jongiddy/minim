class face:

    __mapping = {}

    def __init__(self, provider):
        self._minter_face_provider = provider

    @classmethod
    def implementation(face, cls):
        if __debug__:
            for icls in face.mro():
                if icls.__class__ is face:
                    # No more subclasses
                    break
                elif issubclass(icls, face):
                    classes = face.__mapping.setdefault(icls, ())
                    for existing in classes:
                        if issubclass(cls, existing):
                            break
                    else:
                        face.__mapping[icls] = classes + (cls,)

    @classmethod
    def cast(face, provider):
        """Cast the object to this interface."""
        if __debug__:
            if provider.__class__ is face:
                # cast of interface to same interface
                return provider
            if isinstance(provider, face):
                # provider is a subclass interface
                return face(provider)
            if isinstance(provider, face.__mapping[face]):
                return face(provider)
            raise TypeError(
                'Object {} does not support interface {}'. format(
                    provider, face.__name__))
        # If  we are optimised, just return the object
        return provider

    def __getattribute__(self, name):
        get = super().__getattribute__
        get(name)
        try:
            return getattr(get('_minter_face_provider'), name)
        except AttributeError:
            raise AttributeError(
                'Object {} claims support for interface {} '
                'but does not provide attribute {}'.format(
                    get('__provider'), get('__class__').__name__, name))
