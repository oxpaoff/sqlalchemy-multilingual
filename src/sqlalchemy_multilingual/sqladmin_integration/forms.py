from typing import (
    Any,
    Dict,
    Optional,
    Sequence,
    Type, List, Tuple,
)

import anyio
from sqladmin.ajax import QueryAjaxModelLoader
from sqladmin.forms import ModelConverter, ModelConverterBase, WTFORMS_ATTRS
from sqladmin.helpers import is_async_session_maker
from sqlalchemy import inspect as sqlalchemy_inspect, select
from sqlalchemy.orm import sessionmaker, RelationshipProperty
from wtforms import (
    Field,
    Form,
)
from wtforms.utils import unset_value

from sqlalchemy_multilingual.mixins import TranslatableMixin


class TranslationModelConverter(ModelConverter):

    async def _prepare_select_options(
            self,
            prop: RelationshipProperty,
            session_maker: sessionmaker,
    ) -> List[Tuple[str, Any]]:
        from sqlalchemy.orm import joinedload
        target_model = prop.mapper.class_
        stmt = select(target_model)
        if hasattr(target_model, "translations"):
            stmt = stmt.options(joinedload(target_model.translations))

        if is_async_session_maker(session_maker):
            async with session_maker() as session:
                objects = await session.execute(stmt)
                return [
                    (str(self._get_identifier_value(obj)), str(obj))
                    for obj in objects.scalars().unique().all()
                ]
        else:
            with session_maker() as session:
                objects = await anyio.to_thread.run_sync(session.execute, stmt)
                return [
                    (str(self._get_identifier_value(obj)), str(obj))
                    for obj in objects.scalars().unique().all()
                ]


async def get_model_form(
    model: type,
    session_maker: sessionmaker,
    only: Optional[Sequence[str]] = None,
    exclude: Optional[Sequence[str]] = None,
    column_labels: Optional[Dict[str, str]] = None,
    form_args: Optional[Dict[str, Dict[str, Any]]] = None,
    form_widget_args: Optional[Dict[str, Dict[str, Any]]] = None,
    form_class: Type[Form] = Form,
    form_overrides: Optional[Dict[str, Type[Field]]] = None,
    form_ajax_refs: Optional[Dict[str, QueryAjaxModelLoader]] = None,
    form_include_pk: bool = False,
    form_converter: Type[ModelConverterBase] = TranslationModelConverter,
) -> Type[Form]:
    type_name = model.__name__ + "Form"
    converter = form_converter()
    mapper = sqlalchemy_inspect(model)
    form_args = form_args or {}
    form_widget_args = form_widget_args or {}
    column_labels = column_labels or {}
    form_overrides = form_overrides or {}
    form_ajax_refs = form_ajax_refs or {}

    attributes = []
    names = only or mapper.attrs.keys()
    for name in names:
        if exclude and name in exclude:
            continue
        attributes.append((name, mapper.attrs[name]))

    if issubclass(model, TranslatableMixin):
        translation_mapper = sqlalchemy_inspect(model.translation_model)
        names = translation_mapper.attrs.keys()
        for name in names:
            if name not in model.translation_fields.keys():
                continue
            for locale in model.locales._member_names_:
                attributes.append((f"{name}_{locale}", translation_mapper.attrs[name]))

    field_dict = {}
    for name, attr in attributes:
        field_args = form_args.get(name, {})
        field_args["name"] = name

        field_widget_args = form_widget_args.get(name, {})
        label = column_labels.get(name, None)
        override = form_overrides.get(name, None)
        field = await converter.convert(
            model=model,
            prop=attr,
            session_maker=session_maker,
            field_args=field_args,
            field_widget_args=field_widget_args,
            label=label,
            override=override,
            form_include_pk=form_include_pk,
            form_ajax_refs=form_ajax_refs,
        )
        if field is not None:
            field_dict_key = WTFORMS_ATTRS.get(name, name)
            field_dict[field_dict_key] = field
    field_dict["process"] = process
    return type(type_name, (form_class,), field_dict)


def process(self, formdata=None, obj: Optional[TranslatableMixin] = None, data=None, extra_filters=None, **kwargs):
    formdata = self.meta.wrap_formdata(self, formdata)

    if data is not None:
        kwargs = dict(data, **kwargs)

    filters = extra_filters.copy() if extra_filters is not None else {}

    for name, field in self._fields.items():
        field_extra_filters = filters.get(name, [])

        inline_filter = getattr(self, "filter_%s" % name, None)
        if inline_filter is not None:
            field_extra_filters.append(inline_filter)

        if obj is not None and hasattr(obj, name):
            data = getattr(obj, name)
        elif name in kwargs:
            data = kwargs[name]
        else:
            data = unset_value

        if obj is not None:
            unpreffixed_name = name.split("_")[0]
            if unpreffixed_name in obj.translation_fields.keys():
                for locale in obj.locales._member_names_:
                    if locale == name.split("_")[-1].lower():
                        for translation in obj.translations:
                            if translation.locale == locale:
                                data = getattr(translation, unpreffixed_name, unset_value)
        field.process(formdata, data, extra_filters=field_extra_filters)
