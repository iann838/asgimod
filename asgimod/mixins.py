from typing import Type, TypeVar

from django.db import models, DEFAULT_DB_ALIAS
from django.core.exceptions import SynchronousOnlyOperation

from .sync import sync_to_async
from .db import AsyncQuerySet, AsyncManyToManyRelatedQuerySet, AsyncManyToOneRelatedQuerySet


T = TypeVar("T", bound=models.Model)


class AsyncMixinMeta(models.base.ModelBase):

    def __new__(cls, name, bases, attrs, **kwargs):
        clas: Type[T] = super().__new__(cls, name, bases, attrs, **kwargs)
        clas._asgimod_cached_props = {}
        return clas

    @property
    def aobjects(cls: Type[T]):
        return AsyncQuerySet(cls)

    @property
    def _async_related_fieldmames(cls: Type[T]):
        try:
            return cls._asgimod_cached_props["async_related_fieldmames"]
        except KeyError:
            pass
        fieldnames = set()
        for field in cls._meta.get_fields():
            try:
                fieldnames.add("a" + field.get_accessor_name())
            except AttributeError:
                fieldnames.add("a" + field.name)
        cls._asgimod_cached_props["async_related_fieldmames"] = fieldnames
        return fieldnames


class AsyncMixin(models.Model, metaclass=AsyncMixinMeta):

    def __getattr__(self, attr: str):
        if attr not in self.__class__._async_related_fieldmames:
            raise AttributeError("%r object has no attribute %r" % (self.__class__.__name__, attr))
        try:
            item = getattr(self, attr[1:])
            if not isinstance(item, models.Manager):
                raise SynchronousOnlyOperation
            if "many_to_many" in item.__class__.__mro__[0].__qualname__:
                return AsyncManyToManyRelatedQuerySet(item.model, item)
            return AsyncManyToOneRelatedQuerySet(item.model, item)
        except SynchronousOnlyOperation:
            return sync_to_async(getattr)(self, attr[1:])

    async def asave(self, force_insert=False, force_update=False, using=DEFAULT_DB_ALIAS, update_fields=None):
        return await sync_to_async(self.save)(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    async def adelete(self, using=DEFAULT_DB_ALIAS, keep_parents=False):
        return await sync_to_async(self.delete)(using=using, keep_parents=keep_parents)

    class Meta:
        abstract = True
