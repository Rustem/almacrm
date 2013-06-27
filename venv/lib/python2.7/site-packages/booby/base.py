from booby import validators as builtin_validators


class Field(object):
    """This is the base class for all :mod:`booby.fields`. This class
    can also be used as field in any :class:`models.Model` declaration.

    :param default: This field default value.
    :param required: If `True` this field value should not be `None`.
    :param choices: A `list` of values where this field value should be in.
    :param \*validators: A list of field :mod:`validators` as positional arguments.

    """

    def __init__(self, *validators, **kwargs):
        self.options = kwargs

        self.default = kwargs.get('default')

        # Setup field validators
        self.validators = []
        if kwargs.get('required'):
            self.validators.append(builtin_validators.Required())

        choices = kwargs.get('choices')

        if choices:
            self.validators.append(builtin_validators.In(choices))

        self.validators.extend(validators)

    def __get__(self, instance, owner):
        if instance is not None:
            return instance._data.get(self, self.default)
        return self

    def __set__(self, instance, value):
        instance._data[self] = value

    def to_plain(self, value):
        """Returns a serializable value"""
        return value

    def to_python(self, value):
        """Converts plain value to python value"""
        return value

    def validate(self, value):
        for validator in self.validators:
            validator.validate(value)


class ModelMeta(type):
    def __new__(cls, name, bases, attrs):
        attrs['_fields'] = {}

        for base in bases:
            for k, v in base.__dict__.iteritems():
                if isinstance(v, Field):
                    attrs['_fields'][k] = v

        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                attrs['_fields'][k] = v

        return super(ModelMeta, cls).__new__(cls, name, bases, attrs)
