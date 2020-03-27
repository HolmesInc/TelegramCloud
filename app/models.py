import json
from collections import deque
from datetime import datetime
from mongoengine import (Document, StringField, DateTimeField, ReferenceField, ListField,
                         IntField, FloatField, QuerySet, signals, EmbeddedDocumentField)
from mongoengine.errors import DoesNotExist
from app.config import MONGO_ENGINE_ALIAS


def apply_signal(event):
    """Signal decorator to allow use of callback functions as class decorators."""

    def decorator(function):
        def apply(cls):
            event.connect(function, sender=cls)
            return cls

        function.apply = apply
        return function

    return decorator


@apply_signal(signals.pre_bulk_insert)
def datetime_for_pre_bulk_insert(cls, documents, **kwargs):
    deque(map(BaseFieldsMixin.add_datetime_fields, documents))


@apply_signal(signals.pre_save)
def datetime_for_pre_save(sender, document):
    BaseFieldsMixin.add_datetime_fields(document)


class QueryMixin:
    def to_json(self) -> dict:
        if hasattr(self, 'to_json'):
            data = super().to_json()
            return json.loads(data)
        else:
            raise AttributeError(f'Given object does now have attribute .to_json()')


class AdditionalOperationsMixin:
    @classmethod
    def create(cls, fields: dict, *args, **kwargs) -> object:
        return cls(**fields)

    @classmethod
    def get_id(cls, instance: object) -> str:
        return str(instance.id)

    @classmethod
    def get_all(cls, ids: set):
        return cls.objects(id__in=ids)


class BaseFieldsMixin:
    created = DateTimeField(null=False)
    updated = DateTimeField()

    @staticmethod
    def add_datetime_fields(instance):
        """ Fill 'created' and 'updated' fields with data

        :param instance: model instance to add datetime info
        """
        if not instance.created:
            instance.created = datetime.utcnow()
        instance.updated = datetime.utcnow()


class CustomQuerySet(QueryMixin, QuerySet):
    def get(self, *q_objs, **query):
        try:
            return super().get(*q_objs, **query)
        except DoesNotExist:
            return None


@datetime_for_pre_bulk_insert.apply
@datetime_for_pre_save.apply
class File(BaseFieldsMixin, AdditionalOperationsMixin, QueryMixin, Document):
    telegram_id = StringField(required=True, null=False, unique=True)

    meta = {
        "db_alias": MONGO_ENGINE_ALIAS,
        "collections": "filesystem",
        "queryset_class": CustomQuerySet
    }


@datetime_for_pre_bulk_insert.apply
@datetime_for_pre_save.apply
class Directory(BaseFieldsMixin, AdditionalOperationsMixin, QueryMixin, Document):
    name = StringField(required=True, null=False, unique=True)

    contains_items = ListField(ReferenceField(File))

    meta = {
        "db_alias": MONGO_ENGINE_ALIAS,
        "collections": "filesystem",
        "queryset_class": CustomQuerySet
    }
