# -*- coding: utf-8 -*-
#
# Copyright 2012 Jaime Gil de Sagredo Luna
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The `fields` module contains a list of `Field` classes
for model's definition.

The example below shows the most common fields and builtin validations::

    class Token(Model):
        key = StringField()
        secret = StringField()

    class User(Model):
        login = StringField(required=True)
        name = StringField()
        role = StringField(choices=['admin', 'moderator', 'user'])
        email = EmailField(required=True)
        token = EmbeddedField(Token, required=True)
        is_active = BooleanField(default=False)
"""

from booby import validators as builtin_validators
from booby.base import Field
from booby.models import Model
from booby.errors import BoobyError
import datetime
import inspect


class StringField(Field):
    """:class:`Field` subclass with builtin `string` validation."""

    def __init__(self, *args, **kwargs):
        super(StringField, self).__init__(builtin_validators.String(), *args, **kwargs)


class IntegerField(Field):
    """:class:`Field` subclass with builtin `integer` validation."""

    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__(builtin_validators.Integer(), *args, **kwargs)
        min_value = kwargs.get('min_value')
        max_value = kwargs.get('max_value')
        if min_value:
            self.validators.append(builtin_validators.Min(min_value))
        if max_value:
            self.validators.append(builtin_validators.Max(max_value))

    def __set__(self, instance, value):
        try:
            if value is not None:
                value = int(value)
        except ValueError:
            raise BoobyError("Should contain only integer values.")
        super(IntegerField, self).__set__(instance, value)


class FloatField(Field):
    """:class:`Field` subclass with builtin `float` validation."""

    def __init__(self, *args, **kwargs):
        super(FloatField, self).__init__(builtin_validators.Float(), *args, **kwargs)
        min_value = kwargs.get('min_value')
        max_value = kwargs.get('max_value')
        if min_value:
            self.validators.append(builtin_validators.Min(min_value))
        if max_value:
            self.validators.append(builtin_validators.Max(max_value))


class BooleanField(Field):
    """:class:`Field` subclass with builtin `bool` validation."""

    def __init__(self, *args, **kwargs):
        super(BooleanField, self).__init__(builtin_validators.Boolean(), *args, **kwargs)


class EmbeddedField(Field):
    """:class:`Field` subclass with builtin embedded :class:`models.Model`
    validation.

    """

    def __init__(self, model, *args, **kwargs):
        super(EmbeddedField, self).__init__(builtin_validators.Model(model),
            *args, **kwargs)

        self.model = model

    def __set__(self, instance, value):
        if isinstance(value, dict):
            value = self.model(**value)

        super(EmbeddedField, self).__set__(instance, value)

    def to_plain(self, value):
        return value and value.to_plain() or None


def fetch_model(validators):
    inner_validators, model_validators = [], []
    model = None
    all_classes = tuple(v[1] for v in inspect.getmembers(
        builtin_validators, inspect.isclass))
    for validator in validators:
        if inspect.isclass(validator) and issubclass(validator, Model):
            if model is not None:
                raise BoobyError('In list field there must '
                    'be only one model validator')
            model = validator
            model_validators.append(builtin_validators.Model(validator))
        elif isinstance(validator, builtin_validators.Model):
            if model is not None:
                raise BoobyError('In list field there must '
                    'be only one model validator')
            model = validator.model
            model_validators.append(validator)
        elif isinstance(validator, all_classes):
            inner_validators.append(validator)
    return model, model_validators, inner_validators


def ensure_iterable(value):
    if not value:
        return ()
    if not isinstance(value, (tuple, list)):
        value = (value,)
    return value


class ListField(Field):
    """:class:`Field` subclass validates a list of another fields or models.

    Parameters:
    ----------
    ``validators`` - iterable
        Should contain one subclass of  models.Model or
        one subclass of builtin validators
    """
    def __init__(self, validators, *args, **kwargs):
        validators = ensure_iterable(validators)
        self.model, validators, inner_validators = fetch_model(validators)
        if(not validators):
            validators = inner_validators
        super(ListField, self).__init__(
            builtin_validators.List(*validators),
            **kwargs)

    def __set__(self, instance, value):
        if isinstance(value, (list, tuple)) and len(value) and self.model:
            if not isinstance(value[0], self.model):
                value = self.to_python(value)

        super(ListField, self).__set__(instance, value)

    def to_plain(self, value):
        return value and map(lambda s: isinstance(s, Model) \
            and s.to_plain() or s, value) or None

    def to_python(self, value):
        return value and map(lambda s: self.model and \
            self.model(**s) or s, value) or value


class DateTimeField(Field):
    """:class:`Field` subclass validates a list of another fields or models.
    """
    def __init__(self, *args, **kwargs):
        super(DateTimeField, self).__init__(builtin_validators.DateTime(),
            *args, **kwargs)
        self.format = self.options.get('format', '%Y-%m-%d %H:%M:%S')

    def to_plain(self, value):
        return value and value.strftime(self.format) or value

    def to_python(self, value):
        if(isinstance(value, datetime.datetime)):
            return value
        return value and datetime.datetime.strptime(value, self.format) or None


class DictField(Field):
    """:class:`Field` subclass validates a dict of another fields or models.
    """
    def __init__(self, key=None, value=None, *args, **kwargs):
        super(DictField, self).__init__(builtin_validators.Dict(),
            *args, **kwargs)
        key = ensure_iterable(key)
        value = ensure_iterable(value)
        self.key_model, self.key_validators, _ = fetch_model(key)
        self.value_model, self.value_validators, _ = fetch_model(value)

    def __set__(self, instance, value):
        if isinstance(value, dict) and len(value) \
        and (self.key_model or self.value_model):
            first_key, first_value = value.iteritems().next()
            if (self.value_model and not isinstance(first_value, self.value_model)) \
            or (self.key_model and not isinstance(first_key, self.key_model)):
                value = self.to_python(value)

        super(DictField, self).__set__(instance, value)

    def validate(self, value):
        super(DictField, self).validate(value)
        if value and (self.key_validators or self.value_validators):
            for key, value in value.iteritems():
                for validator in self.key_validators:
                    validator.validate(key)
                for validator in self.value_validators:
                    validator.validate(value)

    def to_plain(self, value):
        if not value:
            return None
        result = {}
        for key, value in value.iteritems():
            key = isinstance(key, Model) and key.to_plain() or key
            value = isinstance(value, Model) and value.to_plain() or value
            result[key] = value
        return result

    def to_python(self, value):
        if not value:
            return None
        result = {}
        for key, value in value.iteritems():
            if self.key_model:
                key = self.key_model(**key)
            if self.value_model:
                value = self.value_model(**value)
            result[key] = value
        return result


class EmailField(Field):
    """:class:`Field` subclass with builtin `email` validation."""

    def __init__(self, *args, **kwargs):
        super(EmailField, self).__init__(builtin_validators.Email(), *args, **kwargs)
