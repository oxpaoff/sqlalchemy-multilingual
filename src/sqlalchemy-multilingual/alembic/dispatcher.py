from sqlalchemy import Column, Integer
from sqlalchemy.dialects import postgresql

import alembic
from mixins import TranslatableMixin


@alembic.autogenerate.comparators.dispatch_for("table")
def create_translation_models(
        autogen_context, modify_ops,
        schemaname, tablename, conn_table, metadata_table
):
    Base = alembic.context.config.attributes["Base"]
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if isinstance(cls, TranslatableMixin) and hasattr(cls, "translatable"):
            type('TranslationModel', (Base,), {
                '__tablename__': cls.__tablename__ + "_translation",
                'id': Column(Integer, primary_key=True, autoincrement=True),
                'locale': Column(postgresql.ENUM(TranslatableMixin.locale, create_type=False), nullable=False),
                **cls.translatable
            })
