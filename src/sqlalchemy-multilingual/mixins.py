from enum import Enum
from typing import Type

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Relationship,
    declared_attr,
    relationship,
)

from models import create_model


class TranslatableMixin:
    locales: Enum = None
    default_locale: str = None
    translation_fields: dict
    __translation_model: Type[DeclarativeBase] = None

    def __getattr__(self, item):
        columns = [c.name for c in self.translation_model.__table__.columns]
        try:
            translation = getattr(self, "translations")[0]
        except IndexError:
            if item in columns:
                return ""
        else:
            if item in columns:
                return getattr(translation, item)
        return getattr(super(), item)

    @classmethod
    def find_base_model(cls) -> Type[DeclarativeBase]:
        for parent in cls.__bases__:
            if issubclass(parent, DeclarativeBase):
                return parent
        raise Exception("Cannot find base model")

    @declared_attr
    def translation_model(cls):
        base_model = cls.find_base_model()
        if cls.__translation_model is None:
            cls.__translation_model = create_model(base_model, cls)
            return cls.__translation_model
        else:
            return cls.__translation_model

    @declared_attr
    def translations(cls) -> Mapped[Relationship]:
        model = cls.translation_model
        return relationship(model, backref="object")
