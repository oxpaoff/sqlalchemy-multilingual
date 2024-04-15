from enum import Enum


class TranslatableMixin:
    locale: [Enum]

    def __getattr__(self, item):
        try:
            translation = self.translations[0]
        except IndexError:
            return getattr(super(), item)

        columns = [c.name for c in translation.__class__.__table__.columns]
        if item in columns:
            return getattr(translation, item)
        return getattr(super(), item)
