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

"""The `models` module contains the `booby` highest level abstraction:
the `Model`.

To define a model you should subclass the :class:`Model` class and
add a list of :mod:`fields` as attributes. And then you could instantiate
your `Model` and work with these objects.

Something like this::

    class Repo(Model):
         name = StringField()
         owner = EmbeddedField(User)

    booby = Repo(
        name=u'Booby',
        owner={
            'login': u'jaimegildesagredo',
            'name': u'Jaime Gil de Sagredo'
        })

    print booby.to_json()
    '{"owner": {"login": "jaimegildesagredo", "name": "Jaime Gil de Sagredo"}, "name": "Booby"}'
"""

import anyjson as json

from booby import errors
from booby.base import ModelMeta


class Model(object):
    """The `Model` class. All Booby models should subclass this.

    By default the `Model's` :func:`__init__` takes a list of keyword arguments
    to initialize the `fields` values. If any of these keys is not a `field`
    then raises :class:`errors.FieldError`. Of course you can overwrite the
    `Model's` :func:`__init__` to get a custom behavior.

    You can get or set Model `fields` values in two different ways: through
    object attributes or dict-like items::

        >>> booby.name is booby['name']
        True
        >>> booby['name'] = u'booby'
        >>> booby['foo'] = u'bar'
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        errors.FieldError: foo

    :param \*\*kwargs: Keyword arguments with the fields values to initialize the model.

    """

    __metaclass__ = ModelMeta

    def __new__(cls, *args, **kwargs):
        model = super(Model, cls).__new__(cls)
        model._data = {}

        return model

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            if k not in self._fields:
                self.__raise_field_error(k)

            setattr(self, k, v)

    def __raise_field_error(self, name):
        raise errors.FieldError("'{}' model has no field '{}'".format(
            type(self).__name__, name))

    def __contains__(self, k):
        return k in self._fields

    def __getitem__(self, k):
        if k not in self._fields:
            self.__raise_field_error(k)

        return getattr(self, k)

    def __setitem__(self, k, v):
        if k not in self._fields:
            self.__raise_field_error(k)

        setattr(self, k, v)

    def update(self, dict_=None, plain_=False, **kwargs):
        """This method updates the `model` fields values with the given dict.
        The model can be updated passing a dict object or keyword arguments,
        like the Python's builtin :func:`dict.update`.

        :param dict_: A dict with the new field values.
        :param plain_: True if values are plain values.
        :param \*\*kwargs: Keyword arguments with the new field values.
        """

        if dict_ is not None:
            self._update(dict_, plain=plain_)
        else:
            self._update(kwargs, plain=plain_)

    def _update(self, values, plain=False):
        for k, v in values.iteritems():
            value = k in self and self[k] or None
            if not k in self:
                continue
            if value and isinstance(value, Model) and isinstance(v, dict):
                value._update(v, plain=plain)
            else:
                if plain:
                    self[k] = self._fields[k].to_python(v)
                else:
                    self[k] = v

    def validate(self):
        """This method validates the entire `model`. That is, validates
        all the :mod:`fields` within this model.

        If some `field` validation fails, then this method raises the same
        exception that the :func:`field.validate` method had raised.

        """

        for name, field in self._fields.iteritems():
            field.validate(getattr(self, name))

    def to_dict(self):
        """This method returns the `model` as a `dict`."""

        result = {}
        for field in self._fields:
            value = getattr(self, field)

            if isinstance(value, Model):
                result[field] = value.to_dict()
            else:
                result[field] = value
        return result

    def to_plain(self):
        """This method returns the `model` as a `dict`."""

        result = {}
        for field in self._fields:
            value = getattr(self, field)
            result[field] = self._fields[field].to_plain(value)
        return result

    def to_json(self):
        """This method returns the `model` as a `json string`.

        To build a json-serializable object for this `model` this method
        uses the :func:`Model.to_dict` method.

        """

        return json.dumps(self.to_plain())

    @classmethod
    def from_plain_dict(cls, plain_dict):
        obj = cls()
        obj.update(dict_=plain_dict, plain_=True)
        return obj

    @classmethod
    def from_json(cls, json_string):
        return cls.from_plain_dict(json.loads(json_string))
