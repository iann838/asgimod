from datetime import datetime, date
from typing import Any, Awaitable, Dict, Generic, List, NoReturn, Optional, Tuple, Type, TypeVar, Union

from django.db import models
from django.db.models.query import QuerySet

from .sync import sync_to_async


T = TypeVar("T", bound=models.Model)


class AsyncQuerySet(Generic[T]):

    def __init__(self, cls: Type[T], queryset: Optional[QuerySet[T]] = None) -> None:
        self._cls = cls
        self._queryset = queryset
        self._to_exec = self._queryset if self._queryset is not None else self._cls.objects

    # MAGIC METHODS - ITERATORS ITERABLES

    async def __aiter__(self):
        items = await self.eval()
        for item in items:
            yield item

    def __getitem__(self, val: Union[slice, int, Any]):
        # CAUTION: it is not handling slice steps which would evaluates the sync queryset
        if isinstance(val, slice):
            return self.__class__(self._cls, self._to_exec[val])
        else:
            return self.item(val)

    # MAGIC METHODS - GENERAL

    def __repr__(self):
        return f"<AsyncQuerySet [...{self._cls}]>"

    def __str__(self):
        return f"<AsyncQuerySet [...{self._cls}]>"

    def __len__(self) -> NoReturn:
        raise NotImplementedError("'AsyncQuerySet' does not support `__len__()`, use `.count()` instead")

    def __bool__(self) -> NoReturn:
        raise NotImplementedError("'AsyncQuerySet' does not support `__bool__()`, use `.exists()` instead")

    # MAGIC METHODS - OPERATORS

    def __and__(self, val: "AsyncQuerySet[T]"):
        return self.__class__(self._cls, self._to_exec & val._to_exec)

    def __or__(self, val: "AsyncQuerySet[T]"):
        return self.__class__(self._cls, self._to_exec | val._to_exec)

    # METHODS FOR EVALUATION OF QUERYSETS

    async def item(self, val: Union[int, Any]):
        return (await self.eval())[val]

    def eval(self) -> Awaitable[Union[List[T], Dict[str, Any], List[Tuple], List, List[datetime], List[date]]]:
        return sync_to_async(list)(self._to_exec)

    # METHODS THAT RETURNS QUERYSETS

    def filter(self, *args, **kwargs):
        return self.__class__(self._cls, self._to_exec.filter(*args, **kwargs))

    def exclude(self, *args, **kwargs):
        return self.__class__(self._cls, self._to_exec.exclude(*args, **kwargs))

    def annotate(self, *args, **kwargs):
        return self.__class__(self._cls, self._to_exec.annotate(*args, **kwargs))

    def alias(self, *args, **kwargs):
        return self.__class__(self._cls, self._to_exec.alias(*args, **kwargs))

    def order_by(self, *fields):
        return self.__class__(self._cls, self._to_exec.order_by(*fields))

    def reverse(self):
        return self.__class__(self._cls, self._to_exec.reverse())

    def distinct(self, *fields):
        return self.__class__(self._cls, self._to_exec.distinct(*fields))

    def values(self, *fields, **expressions):
        return self.__class__(self._cls, self._to_exec.values(*fields, **expressions))

    def values_list(self, *fields, flat=False, named=False):
        return self.__class__(self._cls, self._to_exec.values_list(*fields, flat=flat, named=named))

    def dates(self, field, kind, order='ASC'):
        return self.__class__(self._cls, self._to_exec.dates(field, kind, order=order))

    def datetimes(self, field_name, kind, order='ASC', tzinfo=None, is_dst=None):
        return self.__class__(self._cls, self._to_exec.datetimes(field_name, kind, order=order, tzinfo=tzinfo, is_dst=is_dst))

    def none(self):
        return self.__class__(self._cls, self._to_exec.none())

    def all(self):
        return self.__class__(self._cls, self._to_exec.all())

    def union(self, *other_qs: "AsyncQuerySet[T]", all=False):
        return self.__class__(self._cls, self._to_exec.union(*[qs._to_exec for qs in other_qs], all=all))

    def intersection(self, *other_qs: "AsyncQuerySet[T]"):
        return self.__class__(self._cls, self._to_exec.intersection(*[qs._to_exec for qs in other_qs]))

    def difference(self, *other_qs: "AsyncQuerySet[T]"):
        return self.__class__(self._cls, self._to_exec.difference(*[qs._to_exec for qs in other_qs]))

    def select_related(self, *fields):
        return self.__class__(self._cls, self._to_exec.select_related(*fields))

    def prefetch_related(self, *lookups):
        return self.__class__(self._cls, self._to_exec.prefetch_related(*lookups))

    def extra(self, select=None, where=None, params=None, tables=None, order_by=None, select_params=None):
        return self.__class__(self._cls, self._to_exec.extra(select=select, where=where, params=params, tables=tables, order_by=order_by, select_params=select_params))

    def defer(self, *fields):
        return self.__class__(self._cls, self._to_exec.defer(*fields))

    def only(self, *fields):
        return self.__class__(self._cls, self._to_exec.only(*fields))

    def using(self, alias):
        return self.__class__(self._cls, self._to_exec.using(alias))

    def select_for_update(self, nowait=False, skip_locked=False, of=(), no_key=False):
        return self.__class__(self._cls, self._to_exec.select_for_update(nowait=nowait, skip_locked=skip_locked, of=of, no_key=no_key))

    def raw(self, raw_query, params=(), translations=None, using=None):
        return self.__class__(self._cls, self._to_exec.raw(raw_query, params=params, translations=translations, using=using))

    # METHODS THAT DOES NOT RETURN QUERYSETS

    @sync_to_async
    def get(self, **kwargs):
        return self._to_exec.get(**kwargs)

    @sync_to_async
    def create(self, **kwargs):
        return self._to_exec.create(**kwargs)

    @sync_to_async
    def get_or_create(self, **kwargs):
        return self._to_exec.get_or_create(**kwargs)

    @sync_to_async
    def update_or_create(self, defaults=None, **kwargs):
        return self._to_exec.update_or_create(defaults=defaults, **kwargs)

    @sync_to_async
    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        return self._to_exec.bulk_create(objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts)

    @sync_to_async
    def bulk_update(self, objs, fields, batch_size=None):
        return self._to_exec.bulk_update(objs, fields, batch_size=batch_size)

    @sync_to_async
    def count(self):
        return self._to_exec.count()

    @sync_to_async
    def in_bulk(self, id_list=None, *, field_name='pk'):
        return self._to_exec.in_bulk(id_list=id_list, field_name=field_name)

    @sync_to_async
    def iterator(self, chunk_size=2000):
        return self._to_exec.iterator(chunk_size=chunk_size)

    @sync_to_async
    def latest(self, *fields):
        return self._to_exec.latest(*fields)

    @sync_to_async
    def earliest(self, *fields):
        return self._to_exec.earliest(*fields)

    @sync_to_async
    def first(self):
        return self._to_exec.first()

    @sync_to_async
    def last(self):
        return self._to_exec.last()

    @sync_to_async
    def aggregate(self, *args, **kwargs):
        return self._to_exec.aggregate(*args, **kwargs)

    @sync_to_async
    def exists(self):
        return self._to_exec.exists()

    @sync_to_async
    def update(self, **kwargs):
        return self._to_exec.update(**kwargs)

    @sync_to_async
    def delete(self):
        return self._to_exec.delete()

    @sync_to_async
    def explain(self, format=None, **options):
        return self._to_exec.explain(format=format, **options)


class AsyncManyToOneRelatedQuerySet(AsyncQuerySet[T]):

    @sync_to_async
    def add(self, *objs, bulk=True) -> None:
        return self._to_exec.add(*objs, bulk=bulk)

    @sync_to_async
    def remove(self, *objs, bulk=True) -> None:
        return self._to_exec.remove(*objs, bulk=bulk)

    @sync_to_async
    def clear(self, *, bulk=True) -> None:
        return self._to_exec.clear(bulk=bulk)

    @sync_to_async
    def set(self, objs, *, bulk=True, clear=False) -> None:
        return self._to_exec.set(objs, bulk=bulk, clear=clear)


class AsyncManyToManyRelatedQuerySet(AsyncQuerySet[T]):

    @sync_to_async
    def add(self, *objs, through_defaults=None) -> None:
        return self._to_exec.add(*objs, through_defaults=through_defaults)

    @sync_to_async
    def create(self, *, through_defaults=None, **kwargs) -> T:
        return self._to_exec.create(through_defaults=through_defaults, **kwargs)

    @sync_to_async
    def get_or_create(self, *, through_defaults=None, **kwargs) -> T:
        return self._to_exec.get_or_create(through_defaults=through_defaults, **kwargs)

    @sync_to_async
    def update_or_create(self, *, through_defaults=None, **kwargs) -> T:
        return self._to_exec.update_or_create(through_defaults=through_defaults, **kwargs)

    @sync_to_async
    def remove(self, *objs) -> None:
        return self._to_exec.remove(*objs)

    @sync_to_async
    def clear(self) -> None:
        return self._to_exec.clear()

    @sync_to_async
    def set(self, objs, *, clear=False, through_defaults=None) -> None:
        return self._to_exec.set(objs, clear=clear, through_defaults=through_defaults)


AsyncManager = AsyncQuerySet
AsyncManyToOneRelatedManager = AsyncManyToOneRelatedQuerySet
AsyncManyToManyRelatedManager = AsyncManyToManyRelatedQuerySet
