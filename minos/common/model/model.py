"""
Copyright (C) 2021 Clariteia SL

This file is part of minos framework.

Minos framework can not be copied and/or distributed without the express permission of Clariteia SL.
"""

import datetime
import uuid
import typing as t

from ..exceptions import MinosModelException
from ..logs import log
from .types import Fixed, Enum
from .fields import ModelField

BOOLEAN = "boolean"
NULL = "null"
INT = "int"
FLOAT = "float"
LONG = "long"
DOUBLE = "double"
BYTES = "bytes"
STRING = "string"
ARRAY = "array"
ENUM = "enum"
MAP = "map"
FIXED = "fixed"
DATE = "date"
TIME_MILLIS = "time-millis"
TIMESTAMP_MILLIS = "timestamp-millis"
UUID = "uuid"
DECIMAL = "decimal"

PYTHON_TYPE_TO_AVRO = {
    bool: BOOLEAN,
    type(None): NULL,
    int: LONG,
    float: DOUBLE,
    bytes: BYTES,
    str: STRING,
    list: ARRAY,
    tuple: ARRAY,
    dict: MAP,
    Fixed: {"type": FIXED},
    Enum: {"type": ENUM},
    datetime.date: {"type": INT, "logicalType": DATE},
    datetime.time: {"type": INT, "logicalType": TIME_MILLIS},
    datetime.datetime: {"type": LONG, "logicalType": TIMESTAMP_MILLIS},
    uuid.uuid4: {"type": STRING, "logicalType": UUID},
}

PYTHON_INMUTABLE_TYPES = (str, int, bool, float, bytes, type(None))
PYTHON_LIST_TYPES = (list, tuple)
PYTHON_ARRAY_TYPES = (dict,)


# def _process_aggregate(cls):
#     """
#     Get the list of the class arguments and define it as an AggregateField class
#     """
#     cls_annotations = cls.__dict__.get('__annotations__', {})
#     aggregate_fields = []
#     for name, type in cls_annotations.items():
#         attribute = getattr(cls, name, None)
#         aggregate_fields.append(
#             AggregateField(name=name, type=type, value=attribute)
#         )
#     setattr(cls, "_FIELDS", aggregate_fields)
#
#     # g get metaclass
#     meta_class = getattr(cls, "Meta", None)
#     if meta_class:
#         # meta class exist so get the informations related
#         ...
#     return cls
#
#
# def aggregate(cls=None):
#     def wrap(cls):
#         return _process_aggregate(cls)
#
#     if cls is None:
#         return wrap
#
#     return wrap(cls)

class MinosModel(object):
    """Base class for ``minos`` model entities."""
    _fields: dict[str, ModelField] = {}

    def __init__(self):
        self._fields = self._list_fields()

    @property
    def fields(self) -> dict[str, ModelField]:
        """Fields getter"""
        return self._fields

    def __setattr__(self, key, value):
        if self._fields is not None and key in self._fields:
            field_class: ModelField = self._fields[key]
            field_class.value = value
            self._fields[key] = field_class
            super().__setattr__(key, field_class.value)
        elif key == "_fields":
            super().__setattr__(key, value)
        else:
            raise MinosModelException(f"model attribute {key} doesn't exist")

    def _list_fields(self) -> t.Dict[str, ModelField]:
        fields: t.Dict[str, t.Any] = t.get_type_hints(self)
        fields = self._update_from_inherited_class(fields)
        # get the updated list of field, now is time to convert in a Dictionary of ModelField's
        dict_objects = {}
        for name, type_val in fields.items():
            dict_objects[name] = ModelField(name=name, type_val=type_val, value=None)
        return dict_objects

    def _update_from_inherited_class(self, fields: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """
        get all the child class __annotations__ and update the FIELD base attribute
        """
        for b in self.__class__.__mro__[-1:0:-1]:
            base_fields = getattr(b, "_fields", None)
            if base_fields is not None:
                list_fields = t.get_type_hints(b)
                list_fields.pop("_fields")
                log.debug(f"Fields Derivative {list_fields}")
                if "_fields" not in list_fields:
                    # the class is a derivative of MinosModel class
                    fields |= list_fields
        return fields

    def __eq__(self, other: "MinosModel") -> bool:
        return type(self) == type(other) and tuple(self) == tuple(other)

    def __hash__(self) -> int:
        return hash(tuple(self))

    def __iter__(self) -> t.Iterable:
        # noinspection PyRedundantParentheses
        yield from self.fields.items()
