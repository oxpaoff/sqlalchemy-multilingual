from typing import Type

from sqlalchemy.orm import DeclarativeBase

from sqlalchemy_multilingual.mixins import TranslatableMixin
from sqlalchemy_multilingual.models import create_model


def create_translation_models(base_model: Type[DeclarativeBase]) -> None:
    for mapper in base_model.registry.mappers:
        cls = mapper.class_
        if issubclass(cls, TranslatableMixin) and hasattr(
            cls, "translation_fields"
        ):
            create_model(base_model, cls)
