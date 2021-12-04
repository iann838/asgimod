# asgimod
[![MIT Licensed](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/paaksing/asgimod/blob/master/LICENSE)

This package includes components and utilities that makes django \*usable\* in async python, such as:

- Async model mixin~~s~~ (fully typed), `asgimod.mixins`.
- Async managers and querysets (fully typed), `asgimod.db`.
- Typed `sync_to_async` and `async_to_sync` wrappers, `asgimod.sync`.

#### Package FAQ:

1. Does this support foreign relation access: YES.
2. Does this allow queryset chaining: YES.
3. Does this allow queryset iterating, slicing and indexing: YES.
4. Does this affect default model manager functionality: NO, because it’s on another classproperty `aobjects`.
5. Is everything TYPED: YES, with the only exception of function parameters specification on Python<3.10 since PEP 612 is being released on 3.10.

#### Requirements:

- Django >= 3.0
- Python >= 3.8

#### Installation:

```sh
pip install asgimod
```

The documentation uses references from these model definitions:

```python
class Topping(AsyncMixin, models.Model):
    name = models.CharField(max_length=30)


class Box(AsyncMixin, models.Model):
    name = models.CharField(max_length=50)


class Price(AsyncMixin, models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    currency = models.CharField(max_length=16, default="usd")


class Pizza(AsyncMixin, models.Model):
    name = models.CharField(max_length=50)
    toppings = models.ManyToManyField(Topping)
    box = models.ForeignKey(Box, null=True, on_delete=models.SET_NULL)
    price = models.OneToOneField(Price, on_delete=models.CASCADE)
```

and the following TypeVar:

```python
T = TypeVar("T", bound=models.Model)
```

<br>

---

## Async model mixin~~s~~

This mixin adds async capabilities to the model class and instances:
- `aobjects` full featured async manager.
- `asave`, `adelete` async equivalents of `save` and `delete`.
- `a(.*)` async foreign relations access.

 Import:

```python
from asgimod.mixins import AsyncMixin
```

Usage:

```python
class SampleModel(AsyncMixin, models.Model):
    sample_field = models.CharField(max_length=50)
```

### API Reference:

Extends from `models.Model`, uses metaclass `AsyncMixinMeta` (extended from `models.ModelBase`).

<br>

#### _classproperty_ `aobjects` -> `AsyncManager`
Returns an instance of `AsyncManager`. Async equivalent of `Model.objects`.

<br>

#### _asyncmethod_ `asave(force_insert=False, force_update=False, using=DEFAULT_DB_ALIAS, update_fields=None)` -> None
Async equivalent of `Model.save`

<br>

#### _asyncmethod_ `adelete(using=DEFAULT_DB_ALIAS, keep_parents=False)` -> None
Async equivalent of `Model.delete`

<br>

#### _getattr_ `a(.*)` -> ` Awaitable[T] | AsyncManyToOneRelatedManager | AsyncManyToManyRelatedManager`
There are 3 possible returns from an async foreign relation access.
- `AsyncManyToOneRelatedManager`: Result of a reverse many to one relation access.
- `AsyncManyToManyRelatedManager`: Result of a many to many relation access (both forward and reverse access).
- `Awaitable[T]`: Result of a one to one relation access or a forward many to one relation access. Returns an awaitable with `T` return (`T` being the type of the foreign object).

To access a foreign relation in async mode, add the `a` prefix to your sync access attribute. Using the models defined for this documentations, examples:

```python
price = await Price.aobjects.get(id=1)
pizza = await Pizza.aobjects.get(id=1)
weird_pizza = await Pizza.aobjects.get(id=2)
bacon = await Topping.aobjects.get(id=1)
mushroom = await Topping.aobjects.get(id=2)
medium_box = await Box.aobjects.get(id=1)

# one to one rel
await pizza.aprice
await price.apizza

# reverse many to one rel
await medium_box.apizza_set.all().get(id=1)
await medium_box.apizza_set.filter(id__gt=1).order_by("name").count()
await medium_box.apizza_set.add(weird_pizza)
await medium_box.apizza_set.clear()

# forward many to many rel
await pizza.atoppings.all().exists()
await pizza.atoppings.add(bacon, mushroom)
await bacon.atoppings.filter(name__startswith="b").exists()
await pizza.atoppings.remove(bacon)
await pizza.atoppings.clear()

# reverse many to many rel
await mushroom.apizza_set.all().exists()
await mushroom.apizza_set.add(pizza)
await mushroom.apizza_set.set([pizza, weird_pizza])
```

As you have guessed, these attributes are not defined in code, and thus they are not typed, well, here's the fix:

```python
class Topping(AsyncMixin, models.Model):
    name = models.CharField(max_length=30)
    apizza_set: AsyncManyToManyRelatedManager["Pizza"]

class Box(AsyncMixin, models.Model):
    name = models.CharField(max_length=50)
    apizza_set: AsyncManyToOneRelatedManager["Pizza"]

class Price(AsyncMixin, models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    currency = models.CharField(max_length=16, default="usd")
    apizza: "Pizza"
```

<br>

---

## Async managers and querysets

Async equivalent managers and querysets. All async managers classes are only alias to their respective querysets classes. Such alias exists for user friendliness and better field typings. If you need other methods and attributes unique to managers, use `objects` instead.

Import:

```python
from asgimod.db import (
    AsyncQuerySet,
    AsyncManyToOneRelatedQuerySet,
    AsyncManyToManyRelatedQuerySet,
    AsyncManager,
    AsyncManyToOneRelatedManager,
    AsyncManyToManyRelatedManager
)
```

### API Reference:

### _class_ `AsyncQuerySet[T]` (alias: `AsyncManager[T]`)

<br>

### Magic methods - Iterators & Iterables:

<br>

#### _asynciterator_ `__aiter__` -> `Iterable[T | Tuple | datetime | date | Any]`
Async iterator over an `AsyncQuerySet[T]` using `async for` syntax. The type of the item evaluated queryset depends on the query made, for return type of each query please refer to the official Django QuerySet API references.
```python
async for price in Price.aobjects.filter(currency="usd"):
    self.assertEqual(price.currency, "usd")
```

<br>

#### _getitem_ `__getitem__` -> `AsyncQuerySet[T] | Awaitable[T | Tuple | datetime | date | Any]`
Slicing and indexing over an `AsyncQuerySet[T]` using `[]` syntax.

Slicing an `AsyncQuerySet[T]` will return a new `AsyncQuerySet[T]`, slicing using steps is not allowed, as it would evaluate the internal sync `QuerySet` and raises `SynchronousOnlyOperation`.
```python
prices = await Price.aobjects.all()[:2].eval()
prices = await Price.aobjects.all()[1:2].eval()
prices = await Price.aobjects.all().order_by("-amount")[1:].eval()
```
Indexing an `AsyncQuerySet[T]` will return an `Awaitable[T | Tuple | datetime | date | Any]` (return of the awaitable depends on the query, for return type of each query please refer to the official Django QuerySet API references).
```python
price = await Price.aobjects.all()[0]
price = await Price.aobjects.all()[:5][0]
price = await Price.aobjects.filter(amount__gte=Decimal("9.99"))[0]
```

<br>

### Magic methods - General

<br>

#### _builtin_ `__repr__`
Returns `f"<AsyncQuerySet [...{self._cls}]>"`.

<br>

#### _builtin_ `__str__`
Returns `f"<AsyncQuerySet [...{self._cls}]>"`.

<br>

#### _builtin_ `__len__`
Raises `NotImplementedError`, `AsyncQuerySet` does not support `__len__()`, use `.count()` instead.

<br>

#### _builtin_ `__bool__`
Raises `NotImplementedError`, `AsyncQuerySet` does not support `__bool__()`, use `.exists()` instead.

<br>

### Magic methods - Operators

<br>

#### _operator_ `__and__` (`&`)
`AsyncQuerySet[T] & AsyncQuerySet[T] -> AsyncQuerySet[T]`
```python
# async qs for prices amount > 19.99
qa = Price.aobjects.filter(amount__gt=Decimal("2.99"))
qb = Price.aobjects.filter(amount__gt=Decimal("19.99"))
qs = qa & qb
```

<br>

#### _operator_ `__or__` (`|`)
`AsyncQuerySet[T] | AsyncQuerySet[T] -> AsyncQuerySet[T]`
```python
# async qs for prices with usd and eur currency
qa = Price.aobjects.filter(currency="usd")
qb = Price.aobjects.filter(currency="eur")
qs = qa | qb
```

<br>

### Methods for explicit evaluation of querysets

<br>

#### _asyncmethod_ `item(val: Union[int, Any])` -> `T | Tuple | datetime | date | Any`
Returns the item on index `val` of an `AsyncQuerySet[T]`. This method is used by `__getitem__` internally. The return type depends on the query, for return type of each query please refer to the official Django QuerySet API references.
<br>

#### _asyncmethod_ `eval()` -> `List[T | Tuple | datetime | date | Any]`
Returns the evaluated `AsyncQuerySet[T]` in a list. Equivalent of `sync_to_async(list)(qs: QuerySet[T])`. The item type of the list depends on the query, for return type of each query please refer to the official Django QuerySet API references.
```python
toppings = await Topping.aobjects.all().eval()
toppings_start_with_B = await Topping.aobjects.filter(name__startswith="B").eval()
```

<br>

### Methods that returns a new `AsyncQuerySet[T]` containing the new internal `QuerySet[T]`.
> Used for building queries. These methods are NOT async, it will not connect to the database unless evaluated by other methods or iterations. For return type and in-depth info of each method please refer to the official Django QuerySet API references.

<br>

#### _method_ `filter(*args, **kwargs)`
Equivalent of `models.Manager.filter` and `QuerySet.filter`.

<br>

#### _method_ `exclude(*args, **kwargs)`
Equivalent of `models.Manager.exclude` and `QuerySet.exclude`.

<br>

#### _method_ `annotate(*args, **kwargs)`
Equivalent of `models.Manager.annotate` and `QuerySet.annotate`.

<br>

#### _method_ `alias(*args, **kwargs)`
Equivalent of `models.Manager.alias` and `QuerySet.alias`.

<br>

#### _method_ `order_by(*fields)`
Equivalent of `models.Manager.order_by` and `QuerySet.order_by`.

<br>

#### _method_ `reverse()`
Equivalent of `models.Manager.reverse` and `QuerySet.reverse`.

<br>

#### _method_ `distinct(*fields)`
Equivalent of `models.Manager.distinct` and `QuerySet.distinct`.

<br>

#### _method_ `values(*fields, **expressions)`
Equivalent of `models.Manager.values` and `QuerySet.values`.

<br>

#### _method_ `values_list(*fields, flat=False, named=False)`
Equivalent of `models.Manager.values_list` and `QuerySet.values_list`.

<br>

#### _method_ `dates(field, kind, order='ASC')`
Equivalent of `models.Manager.dates` and `QuerySet.dates`.

<br>

#### _method_ `datetimes(field_name, kind, order='ASC', tzinfo=None, is_dst=None)`
Equivalent of `models.Manager.datetimes` and `QuerySet.datetimes`.

<br>

#### _method_ `none()`
Equivalent of `models.Manager.none` and `QuerySet.none`.

<br>

#### _method_ `all()`
Equivalent of `models.Manager.all` and `QuerySet.all`.

<br>

#### _method_ `union(*other_qs: "AsyncQuerySet[T]", all=False)`
Equivalent of `models.Manager.union` and `QuerySet.union`.

<br>

#### _method_ `intersection(*other_qs: "AsyncQuerySet[T]")`
Equivalent of `models.Manager.intersection` and `QuerySet.intersection`.

<br>

#### _method_ `difference(*other_qs: "AsyncQuerySet[T]")`
Equivalent of `models.Manager.difference` and `QuerySet.difference`.

<br>

#### _method_ `select_related(*fields)`
Equivalent of `models.Manager.select_related` and `QuerySet.select_related`.

<br>

#### _method_ `prefetch_related(*lookups)`
Equivalent of `models.Manager.prefetch_related` and `QuerySet.prefetch_related`.

<br>

#### _method_ `extra(select=None, where=None, params=None, tables=None, order_by=None, select_params=None)`
Equivalent of `models.Manager.extra` and `QuerySet.extra`.

<br>

#### _method_ `defer(*fields)`
Equivalent of `models.Manager.defer` and `QuerySet.defer`.

<br>

#### _method_ `only(*fields)`
Equivalent of `models.Manager.only` and `QuerySet.only`.

<br>

#### _method_ `using(alias)`
Equivalent of `models.Manager.using` and `QuerySet.using`.

<br>

#### _method_ `select_for_update(nowait=False, skip_locked=False, of=(), no_key=False)`
Equivalent of `models.Manager.select_for_update` and `QuerySet.select_for_update`.

<br>

#### _method_ `raw(raw_query, params=(), translations=None, using=None)`
Equivalent of `models.Manager.raw` and `QuerySet.raw`.

<br>

### Methods that does NOT return a new `AsyncQuerySet[T]`.
> These methods are async and will connect to the database. For return type and in-depth info of each method please refer to the official Django QuerySet API references.

<br>

#### _asyncmethod_ `get(**kwargs)`
Async equivalent of `models.Manager.get` and `QuerySet.get`.

<br>

#### _asyncmethod_ `create(**kwargs)`
Async equivalent of `models.Manager.create` and `QuerySet.create`.

<br>

#### _asyncmethod_ `get_or_create(**kwargs)`
Async equivalent of `models.Manager.get_or_create` and `QuerySet.get_or_create`.

<br>

#### _asyncmethod_ `update_or_create(defaults=None, **kwargs)`
Async equivalent of `models.Manager.update_or_create` and `QuerySet.update_or_create`.

<br>

#### _asyncmethod_ `bulk_create(objs, batch_size=None, ignore_conflicts=False)`
Async equivalent of `models.Manager.bulk_create` and `QuerySet.bulk_create`.

<br>

#### _asyncmethod_ `bulk_update(objs, fields, batch_size=None)`
Async equivalent of `models.Manager.bulk_update` and `QuerySet.bulk_update`.

<br>

#### _asyncmethod_ `count()`
Async equivalent of `models.Manager.count` and `QuerySet.count`.

<br>

#### _asyncmethod_ `in_bulk(id_list=None, *, field_name='pk')`
Async equivalent of `models.Manager.in_bulk` and `QuerySet.in_bulk`.

<br>

#### _asyncmethod_ `iterator(chunk_size=2000)`
Async equivalent of `models.Manager.iterator` and `QuerySet.iterator`.

<br>

#### _asyncmethod_ `latest(*fields)`
Async equivalent of `models.Manager.latest` and `QuerySet.latest`.

<br>

#### _asyncmethod_ `earliest(*fields)`
Async equivalent of `models.Manager.earliest` and `QuerySet.earliest`.

<br>

#### _asyncmethod_ `first()`
Async equivalent of `models.Manager.first` and `QuerySet.first`.

<br>

#### _asyncmethod_ `last()`
Async equivalent of `models.Manager.last` and `QuerySet.last`.

<br>

#### _asyncmethod_ `aggregate(*args, **kwargs)`
Async equivalent of `models.Manager.aggregate` and `QuerySet.aggregate`.

<br>

#### _asyncmethod_ `exists()`
Async equivalent of `models.Manager.exists` and `QuerySet.exists`.

<br>

#### _asyncmethod_ `update(**kwargs)`
Async equivalent of `models.Manager.update` and `QuerySet.update`.

<br>

#### _asyncmethod_ `delete()`
Async equivalent of `models.Manager.delete` and `QuerySet.delete`.

<br>

#### _asyncmethod_ `explain(format=None, **options)`
Async equivalent of `models.Manager.explain` and `QuerySet.explain`.

<br>

### _class_ `AsyncManyToOneRelatedQuerySet[T]` (alias: `AsyncManyToOneRelatedManager[T]`)

Extends `AsyncQuerySet[T]`. Manager returned for reverse many-to-one foreign relation access.

<br>

#### _asyncmethod_ `add(*objs, bulk=True) -> None`
Async equivalent of `models.fields.related_descriptors.create_reverse_many_to_one_manager.RelatedManager.add`.

<br>

#### _asyncmethod_ `remove(*objs, bulk=True) -> None`
Async equivalent of `models.fields.related_descriptors.create_reverse_many_to_one_manager.RelatedManager.remove`.

<br>

#### _asyncmethod_ `clear(*, bulk=True) -> None`
Async equivalent of `models.fields.related_descriptors.create_reverse_many_to_one_manager.RelatedManager.clear`.

<br>

#### _asyncmethod_ `set(objs, *, bulk=True, clear=False) -> None`
Async equivalent of `models.fields.related_descriptors.create_reverse_many_to_one_manager.RelatedManager.set`.

<br>

### _class_ `AsyncManyToManyRelatedQuerySet[T]` (alias: `AsyncManyToManyRelatedManager[T]`)

Extends `AsyncQuerySet[T]`. Manager returned for many-to-many foreign relation access.

<br>

#### _asyncmethod_ `add(*objs, through_defaults=None) -> None`
Async equivalent of `models.fields.related_descriptors.create_forward_many_to_many_manager.RelatedManager.add`.

<br>

#### _asyncmethod_ `create(*, through_defaults=None, **kwargs) -> T`
Async equivalent of `models.fields.related_descriptors.create_forward_many_to_many_manager.RelatedManager.create`.

<br>

#### _asyncmethod_ `get_or_create(*, through_defaults=None, **kwargs) -> T`
Async equivalent of `models.fields.related_descriptors.create_forward_many_to_many_manager.RelatedManager.get_or_create`.

<br>

#### _asyncmethod_ `update_or_create(*, through_defaults=None, **kwargs) -> T`
Async equivalent of `models.fields.related_descriptors.create_forward_many_to_many_manager.RelatedManager.update_or_create`.

<br>

#### _asyncmethod_ `remove(*objs) -> None`
Async equivalent of `models.fields.related_descriptors.create_forward_many_to_many_manager.RelatedManager.remove`.

<br>

#### _asyncmethod_ `clear() -> None`
Async equivalent of `models.fields.related_descriptors.create_forward_many_to_many_manager.RelatedManager.clear`.

<br>

#### _asyncmethod_ `set(objs, *, clear=False, through_defaults=None) -> None`
Async equivalent of `models.fields.related_descriptors.create_forward_many_to_many_manager.RelatedManager.set`.

<br>

---

## Typed async and sync wrappers

As of the release of this package the `sync_to_async` and `async_to_sync` wrappers on `asgiref.sync` are not typed, this package provides the typed equivalent of these wrappers:
- If project is on python<3.10, only the return type will be typed.
- If project is on python>=3.10, both the return type and param specs will be typed ([PEP 612](https://www.python.org/dev/peps/pep-0612/)).

Import:

```python
from asgimod.sync import sync_to_async, async_to_sync
```

Usage: Same as `asgiref.sync`

<br>

---

## Contribution & Development

Contributions are welcomed, there are uncovered test cases and probably missing features.

### Typing the missing things in sync Django

Django itself is not doing well at typing, for example the sync managers are not typed, but please keep those out of the scope of this project as it's not related to async and asgi.

### Running the tests

A django test project was used for testing, simply run
```sh
python manage.py shell
```
