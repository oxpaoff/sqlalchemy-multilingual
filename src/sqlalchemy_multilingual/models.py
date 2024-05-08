from typing import Optional, Type, Union, TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import (
    DeclarativeBase,
    MappedColumn,
    InstrumentedAttribute,
    Relationship,
    relationship
)

from sqlalchemy_multilingual.constants import EXCLUDE_COLUMNS
from sqlalchemy_multilingual.exception import UnableToFindPrimaryKey

if TYPE_CHECKING:
    from mixins import TranslatableMixin

def str_method(self: DeclarativeBase) -> str:
    str_data = {}
    for k in self.translation_fields.keys():
        str_data[f"{k}_{self.locale.value.upper()}"] = getattr(self, k)
    return str(str_data)

def create_model(
    base_model: Type[DeclarativeBase],
    cls: Union[Type[DeclarativeBase], "TranslatableMixin"],
) -> Union[Type[DeclarativeBase], type]:
    pk_column_name = get_pk_column(cls)
    if pk_column_name is None:
        raise UnableToFindPrimaryKey

    object_id = f"{cls.__tablename__}.{pk_column_name}"

    cls_name = cls.__name__
    name = f"{cls_name}Translation"

    attributes = {
        "__tablename__": f"{cls.__tablename__}_translation",
        "__table_args__": {"extend_existing": True},
        "id": Column(Integer, primary_key=True, autoincrement=True),
        "locale": Column(
            postgresql.ENUM(cls.locales, create_type=False), nullable=False
        ),
        "object_id": Column(
            Integer, ForeignKey(object_id, ondelete="CASCADE")
        ),
        "__str__": str_method,
        "translation_fields": cls.translation_fields,
        **cls.translation_fields,
    }
    return type(name, (base_model,), attributes)


def get_pk_column(model: Type[DeclarativeBase]) -> Optional[str]:
    class_attrs = dir(model)
    for attr_name in class_attrs:
        if attr_name in EXCLUDE_COLUMNS:
            continue
        if not attr_name.startswith("__") and not attr_name.startswith("_"):
            attr = getattr(model, attr_name)
            if isinstance(attr, MappedColumn) and attr.column.primary_key:
                return attr_name
            elif isinstance(attr, InstrumentedAttribute) and not isinstance(attr.property, Relationship) and attr.primary_key:
                return attr_name
