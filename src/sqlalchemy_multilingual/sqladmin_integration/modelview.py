from typing import Type, Any, ClassVar

from sqladmin.forms import ModelConverterBase
from sqladmin.pagination import Pagination
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy_multilingual.sqladmin_integration.forms import get_model_form, TranslationModelConverter
from starlette.requests import Request
from wtforms import Form

from sqladmin import ModelView


class TranslatableModelView(ModelView):
    form_converter: ClassVar[Type[ModelConverterBase]] = TranslationModelConverter

    async def list(self, request: Request) -> Pagination:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("pageSize", 0))
        page_size = min(page_size or self.page_size, max(self.page_size_options))
        search = request.query_params.get("search", None)

        stmt = self.list_query(request)
        for relation in self._list_relations:
            if hasattr(relation.prop.mapper.class_, "translations"):
                stmt = stmt.options(joinedload(relation).joinedload(relation.prop.mapper.class_.translations))
            else:
                stmt = stmt.options(joinedload(relation))

        stmt = self.sort_query(stmt, request)

        if search:
            stmt = self.search_query(stmt=stmt, term=search)
            count = await self.count(request, select(func.count()).select_from(stmt))
        else:
            count = await self.count(request)

        stmt = stmt.limit(page_size).offset((page - 1) * page_size)
        rows = await self._run_query(stmt)

        pagination = Pagination(
            rows=rows,
            page=page,
            page_size=page_size,
            count=count,
        )

        return pagination

    async def get_object_for_details(self, value: Any) -> Any:
        stmt = self._stmt_by_identifier(value)

        for relation in self._details_relations:
            if hasattr(relation.prop.mapper.class_, "translations"):
                stmt = stmt.options(joinedload(relation).joinedload(relation.prop.mapper.class_.translations))
            else:
                stmt = stmt.options(joinedload(relation))

        return await self._get_object_by_pk(stmt)

    async def scaffold_form(self) -> Type[Form]:
        if self.form is not None:
            return self.form
        return await get_model_form(
            model=self.model,
            exclude=["translations"],
            session_maker=self.session_maker,
            only=self._form_prop_names ,
            column_labels=self._column_labels,
            form_args=self.form_args,
            form_widget_args=self.form_widget_args,
            form_class=self.form_base_class,
            form_overrides=self.form_overrides,
            form_ajax_refs=self._form_ajax_refs,
            form_include_pk=self.form_include_pk,
            form_converter=self.form_converter,
        )

    async def insert_model(self, request: Request, data: dict) -> Any:
        obj = await super().insert_model(request, data)
        await self.insert_translations(obj, data)
        return obj

    async def update_model(self, request: Request, pk: str, data: dict) -> Any:
        obj = await super().update_model(request, pk, data)
        await self.update_translations(obj, data)
        return obj

    async def insert_translations(self, obj: Any, data: dict) -> Any:
        async with self.session_maker(expire_on_commit=False) as session:
            for field in obj.translation_fields.keys():
                for locale in obj.locales._member_names_:
                    new_obj = obj.translation_model(object=obj, locale=locale)
                    setattr(new_obj, field, data.get(f"{field}_{locale}", ""))
                    session.add(new_obj)
            await session.commit()
            return obj

    async def update_translations(self, obj: Any, data: dict) -> Any:
        async with self.session_maker(expire_on_commit=False) as session:
            for translation in obj.translations:
                for field in obj.translation_fields.keys():
                    setattr(translation, field, data.get(f"{field}_{translation.locale}", ""))
                    session.add(translation)
            await session.commit()
            return obj
