import json
import base64
from collections import deque
from datetime import datetime
from mongoengine import (Document, StringField, DateTimeField, ReferenceField, ListField, QuerySet, BinaryField,
                         signals, NULLIFY, CASCADE, PULL)
from mongoengine.errors import DoesNotExist
from app.config import MONGO_ENGINE_ALIAS, CRYPTO


def apply_signal(event):
    """ Signal decorator to allow use of callback functions as class decorators.
    """

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
        """ Convert model instance to JSON representation

        :return: JSON
        """
        if hasattr(self, 'to_json'):
            data = super().to_json()
            return json.loads(data)
        else:
            raise AttributeError(f'Given object does now have attribute .to_json()')


class AdditionalOperationsMixin:
    """ Adds additional operation over data entities
    """
    @classmethod
    def create(cls, fields: dict, *args, **kwargs) -> object:
        """ Create instance of mongo model from dictionary

        :param fields: model fields are keys, data is info that should be saved into DB
        :return: instance of mongo model with data
        """
        return cls(**fields)

    @classmethod
    def get_id(cls, instance: object) -> str:
        """ Get id of given record

        :param instance: model instance with data
        :return: string representation of record id
        """
        return str(instance.id)

    @classmethod
    def get_all(cls, ids: set):
        """ Get all records in given range of ids

        :param ids: ids of records
        :return: instances, that were found by given ids
        """
        return cls.objects(id__in=ids)


class BaseFieldsMixin:
    """ Adds additional fields to each record
    """
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
    """ Modified mongoengine QuerySet class. Created prevent raising exception,
        when there is no data in DB by given key (.get() method)
    """
    def get(self, *q_objs, **query):
        try:
            return super().get(*q_objs, **query)
        except DoesNotExist:
            return None


@datetime_for_pre_bulk_insert.apply
@datetime_for_pre_save.apply
class File(BaseFieldsMixin, AdditionalOperationsMixin, QueryMixin, Document):
    """ Represents File entity, that stores information about telegram file
    """
    telegram_id = BinaryField(required=True, null=False, unique=True)

    meta = {
        "db_alias": MONGO_ENGINE_ALIAS,
        "collections": "filesystem",
        "queryset_class": CustomQuerySet
    }

    def clean(self):
        """ Encrypt telegram_id field before saving
        """
        self.telegram_id = str(self.telegram_id)
        self.telegram_id = CRYPTO.encrypt(self.telegram_id.encode())

    @staticmethod
    def prepare_telegram_id(telegram_id: bytes) -> int:
        """ Convert encrypted string to appropriate telegram message id

        :param telegram_id: encrypted message id
        :return: decrypted message id
        """
        return int(CRYPTO.decrypt(telegram_id))


@datetime_for_pre_bulk_insert.apply
@datetime_for_pre_save.apply
class Directory(BaseFieldsMixin, AdditionalOperationsMixin, QueryMixin, Document):
    """ Representation of directory entity, that stores file ids
    """
    name = StringField(required=True, null=False)
    user_id = BinaryField(required=True, null=False)

    contains_directories = ListField(ReferenceField("self", reverse_delete_rule=PULL))
    contains_files = ListField(ReferenceField(File, reverse_delete_rule=PULL))

    meta = {
        "db_alias": MONGO_ENGINE_ALIAS,
        "collections": "filesystem",
        "queryset_class": CustomQuerySet,
        "indexes": [
            {"fields": ('name', 'user_id'), 'unique': True}
        ]
    }

    def __str__(self):
        return f'Directory name: {self.name}'

    def clean(self):
        """ Encrypt telegram_id field before saving
        """
        if type(self.user_id) == int:
            self.user_id = Directory.encrypt_user_id(self.user_id)

    @staticmethod
    def encrypt_user_id(user_id: int) -> bytes:
        """ Encrypt user ID

        :param user_id: id to encrypt
        :return: encrypted user id
        """
        return base64.b64encode(str(user_id).encode())

    @staticmethod
    def decrypt_user_id(user_id: bytes) -> int:
        """ Convert encrypted string to user id

        :param user_id: id to decrypt
        :return: decrypted user id
        """
        return int(base64.b64decode(user_id).decode())

    def delete(self, signal_kwargs=None, **write_concern):
        def __delete_children(children):
            deque(
                map(lambda instance: instance.delete(), children)
            )

        __delete_children(self.contains_directories)
        __delete_children(self.contains_files)
        super().delete(signal_kwargs, **write_concern)

    def has_subdirectory(self, name: str, encrypted_user_id: bytes) -> bool:
        """ Check that Directory with name <name> exists and is subdirectory of current directory

        :param name: instance of possible subdirectory
        :param encrypted_user_id:
        :return: True if <name> is subdirectory, otherwise False
        """
        if Directory.exists(name, encrypted_user_id):
            testing_subdirectory = Directory.objects.get(name=name, user_id=encrypted_user_id)
            return testing_subdirectory in self.contains_directories
        else:
            return False

    @classmethod
    def exists(cls, name: str, encrypted_user_id: bytes) -> bool:
        if cls.objects.get(name=name, user_id=encrypted_user_id):
            return True

        return False
