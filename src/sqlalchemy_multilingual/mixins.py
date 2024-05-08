from enum import Enum

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Relationship,
    declared_attr,
    relationship,
)
from sqlalchemy_multilingual.models import create_model
from typing import Type


class TranslatableMixin:
    locales: Enum = None
    default_locale: str = None
    translation_fields: dict
    __translation_model: Type[DeclarativeBase] = None

    def __getattr__(self, item):
        columns = [c.name for c in self.translation_model.__table__.columns]
        if item not in columns:
            return getattr(super(), item)
        try:
            translation = getattr(self, "translations")[0]
        except IndexError:
            if item in columns:
                return ""
        else:
            if item in columns:
                return getattr(translation, item)

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

    def __str__(self) -> str:
        default_str = f"{self.__class__.__name__} {self.id}"
        try:
            for translation in self.translations:
                if translation.locale == self.default_locale:
                    return str(translation)
        except SQLAlchemyError:
            return default_str
        return default_str
