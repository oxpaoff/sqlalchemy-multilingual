from typing import Type

from sqlalchemy import ColumnElement, Select, and_, not_, or_
from sqlalchemy.orm import contains_eager

from sqlalchemy_multilingual.exception import NoDefaultLocale
from sqlalchemy_multilingual.mixins import TranslatableMixin


def select_i18n(
    stmt: Select,
    model: Type[TranslatableMixin],
    lang: str,
    load_default: bool = False,
) -> Select:
    condition = where_condition(
        model=model, lang=lang, load_default=load_default
    )
    return (
        stmt.outerjoin(model.translation_model)
        .where(condition)
        .options(contains_eager(model.translations))
    )


def where_condition(
    model: Type[TranslatableMixin], lang: str, load_default: bool
) -> ColumnElement:
    if load_default is True:
        if model.default_locale is None:
            raise NoDefaultLocale
        return or_(
            and_(
                model.translation_model.locale == lang,
                model.translations.any(model.translation_model.locale == lang),
            ),
            and_(
                model.translation_model.locale == model.default_locale,
                model.translation_model.object_id == model.id,
                not_(
                    model.translations.any(
                        model.translation_model.locale == lang
                    )
                ),
            ),
        )
    else:
        return model.translation_model.locale == lang


async def insert_i18n(
    obj: Type[TranslatableMixin],
    session,
    lang: str,
    values: dict,
) -> None:
    translation = obj.translation_model(
        object=obj, **values, locale=lang
    )
    session.add(translation)
