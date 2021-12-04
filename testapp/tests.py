from decimal import Decimal

from django.test import TestCase
from asgimod.sync import async_to_sync

from .models import Pizza, Topping, Price, Box


class AsyncTestCase(TestCase):

    @async_to_sync
    async def setUp(self) -> None:
        price = await Price.aobjects.create(id=1, amount=Decimal("9.99"), currency="usd")
        await Price.aobjects.create(id=2, amount=Decimal("39.99"), currency="usd") # big_price
        await Price.aobjects.create(id=3, amount=Decimal("29.99"), currency="eur") # eur_price
        pizza = await Pizza.aobjects.create(id=1, name="Thicc Pizza", price=price) # pizza
        await Topping.aobjects.create(id=1, name="Bacon") # bacon
        await Topping.aobjects.create(id=2, name="Mushroom") # mushroom
        await Topping.aobjects.create(id=3, name="Random") # random
        medium_box = await Box.aobjects.create(id=1, name="Medium") # medium_box
        pizza.box = medium_box
        await pizza.asave()

    @async_to_sync
    async def test_model_methods(self):
        brocoli = await Topping.aobjects.create(name="Brocoli")
        self.assertEqual(brocoli.name, "Brocoli")
        brocoli.name = "Brocoli 2"
        await brocoli.asave() # save
        brocoli = await Topping.aobjects.get(name="Brocoli 2")
        self.assertEqual(brocoli.name, "Brocoli 2")
        await brocoli.adelete() # delete
        brocoli_exists = await Topping.aobjects.filter(name="Brocoli 2").exists()
        self.assertEqual(brocoli_exists, False)

    @async_to_sync
    async def test_methods_non_queryset(self):
        # CASE get
        pizza = await Pizza.aobjects.get(id=1)
        self.assertEqual(pizza.name, "Thicc Pizza")
        bacon = await Topping.aobjects.get(id=1)
        self.assertEqual(bacon.name, "Bacon")
        mushroom = await Topping.aobjects.get(id=2)
        self.assertEqual(mushroom.name, "Mushroom")

        # CASE create
        price = await Price.aobjects.create(amount=Decimal("19.99"), currency="usd")
        pizza = await Pizza.aobjects.create(name="Smol Pizza", price=price)
        brocoli = await Topping.aobjects.create(name="Brocoli")
        maiz = await Topping.aobjects.create(name="Maiz")
        large_box = await Box.aobjects.create(name="Large")
        self.assertEqual(price.amount, Decimal("19.99"))
        self.assertEqual(price.currency, "usd")
        self.assertEqual(pizza.name, "Smol Pizza")
        self.assertEqual(brocoli.name, "Brocoli")
        self.assertEqual(maiz.name, "Maiz")
        self.assertEqual(large_box.name, "Large")
        await pizza.adelete()
        await price.adelete()
        await brocoli.adelete()
        await large_box.adelete()

        # CASE get_or_create
        sausage, created = await Topping.aobjects.get_or_create(name="Sausage")
        self.assertEqual(sausage.name, "Sausage")
        self.assertEqual(created, True)
        smol_box, created = await Box.aobjects.get_or_create(name="Smol")
        self.assertEqual(smol_box.name, "Smol")
        self.assertEqual(created, True)
        maiz, created = await Topping.aobjects.get_or_create(name="Maiz")
        self.assertEqual(maiz.name, "Maiz")
        self.assertEqual(created, False)
        await sausage.adelete()
        await smol_box.adelete()
        await maiz.adelete()

        # CASE update_or_create
        maiz = await Topping.aobjects.create(name="Maiz")
        maiz, created = await Topping.aobjects.update_or_create(name="Maiz", defaults={"name": "Maiz2"})
        self.assertEqual(maiz.name, "Maiz2")
        self.assertEqual(created, False)
        await maiz.adelete()
        maiz, created = await Topping.aobjects.update_or_create(name="Maiz", defaults={"name": "Maiz2"})
        self.assertEqual(maiz.name, "Maiz2")
        self.assertEqual(created, True)

        # CASE bulk_create
        cursed_toppings = await Topping.aobjects.bulk_create([
            Topping(name="Pineapple"),
            Topping(name="Apple"),
        ])
        self.assertEqual(len(cursed_toppings), 2)
        self.assertEqual(cursed_toppings[0].name, "Pineapple")
        self.assertEqual(cursed_toppings[1].name, "Apple")
        cursed_toppings = await Topping.aobjects.filter(name__in=["Pineapple", "Apple"]).eval()
        self.assertEqual(len(cursed_toppings), 2)
        self.assertEqual(cursed_toppings[0].name, "Pineapple")
        self.assertEqual(cursed_toppings[1].name, "Apple")
        for cursed_topping in cursed_toppings:
            await cursed_topping.adelete()

        # CASE bulk_update
        cursed_toppings = [
            await Topping.aobjects.create(name="Pineapple"),
            await Topping.aobjects.create(name="Apple"),
        ]
        cursed_toppings[0].name = "NO Pineapple"
        cursed_toppings[1].name = "NO Apple"
        await Topping.aobjects.bulk_update(cursed_toppings, fields=["name"])
        cursed_toppings = await Topping.aobjects.filter(name__startswith="NO").eval()
        self.assertEqual(len(cursed_toppings), 2)
        self.assertEqual(cursed_toppings[0].name, "NO Pineapple")
        self.assertEqual(cursed_toppings[1].name, "NO Apple")
        for cursed_topping in cursed_toppings:
            await cursed_topping.adelete()

        # CASE count
        prices_count = await Price.aobjects.filter(currency="usd").count()
        eur_prices_count = await Price.aobjects.filter(currency="eur").count()
        cny_prices_count = await Price.aobjects.filter(currency="cny").count()
        self.assertEqual(prices_count, 2)
        self.assertEqual(eur_prices_count, 1)
        self.assertEqual(cny_prices_count, 0)

        # CASE latest
        latest_price = await Price.aobjects.latest("id")
        self.assertEqual(latest_price.amount, Decimal("29.99"))

        # CASE earliest
        latest_price = await Price.aobjects.earliest("id")
        self.assertEqual(latest_price.amount, Decimal("9.99"))

        # CASE first
        smol_price = await Price.aobjects.order_by("amount").first()
        self.assertEqual(smol_price.amount, Decimal("9.99"))

        # CASE last
        big_price = await Price.aobjects.order_by("amount").last()
        self.assertEqual(big_price.amount, Decimal("39.99"))

        # CASE exists
        usd_prices_exists = await Price.aobjects.filter(currency="usd").exists()
        self.assertEqual(usd_prices_exists, True)
        cny_prices_exists = await Price.aobjects.filter(currency="cny").exists()
        self.assertEqual(cny_prices_exists, False)

        # NOTE: THERE ARE UNCOVERED TEST CASES PENDING TO BE ADDED.

    @async_to_sync
    async def test_methods_queryset(self):
        # CASE all
        toppings = await Topping.aobjects.all().eval()
        self.assertEqual(len(toppings), 3)
        toppings = await Topping.aobjects.all().order_by("id").eval()
        self.assertEqual(toppings[0].name, "Bacon")

        # CASE filter
        prices = await Price.aobjects.filter(currency="usd").eval()
        prices_count = await Price.aobjects.filter(currency="usd").count()
        self.assertEqual(len(prices), 2)
        self.assertEqual(prices_count, 2)
        async for price in Price.aobjects.filter(currency="usd"):
            self.assertEqual(price.currency, "usd")

        # CASE exclude
        non_usd_prices = await Price.aobjects.exclude(currency="usd").eval()
        non_usd_prices_exists = await Price.aobjects.exclude(currency="usd").exists()
        self.assertEqual(len(non_usd_prices), 1)
        self.assertEqual(non_usd_prices_exists, True)
        async for price in Price.aobjects.exclude(currency="usd"):
            self.assertNotEqual(price.currency, "usd")

        # CASE order_by
        prices = await Price.aobjects.filter(currency="usd").order_by("amount").eval()
        prices_count = await Price.aobjects.filter(currency="usd").order_by("amount").count()
        self.assertEqual(len(prices), 2)
        self.assertEqual(prices_count, 2)
        last_ord_price = Decimal("0")
        async for price in Price.aobjects.filter(currency="usd").order_by("amount"):
            self.assertGreater(price.amount, last_ord_price)
            last_ord_price = price.amount

        # CASE reverse
        prices = await Price.aobjects.filter(currency="usd").order_by("amount").reverse().eval()
        prices_count = await Price.aobjects.filter(currency="usd").order_by("amount").reverse().count()
        self.assertEqual(len(prices), 2)
        self.assertEqual(prices_count, 2)
        last_ord_price = Decimal("100")
        async for price in Price.aobjects.filter(currency="usd").order_by("amount").reverse():
            self.assertLess(price.amount, last_ord_price)
            last_ord_price = price.amount

        # CASE distinct
        prices = await Price.aobjects.filter(currency="usd").distinct().eval()
        prices_count = await Price.aobjects.filter(currency="usd").distinct().count()
        self.assertEqual(len(prices), 2)
        self.assertEqual(prices_count, 2)
        # prices = await Price.aobjects.filter(currency="usd").distinct("currency").eval()
        # prices_count = await Price.aobjects.filter(currency="usd").distinct("currency").count()
        # self.assertEqual(len(prices), 1)
        # self.assertEqual(prices_count, 1)
        # DISTINCT ON fields is not supported by this database backend (sqlit3)

        # CASE union
        usd_prices_qs = Price.aobjects.filter(currency="usd")
        eur_prices_qs = Price.aobjects.filter(currency="eur")
        prices_qs = usd_prices_qs.union(eur_prices_qs)
        prices = await prices_qs.eval()
        prices_count = await prices_qs.count()
        self.assertEqual(len(prices), 3)
        self.assertEqual(prices_count, 3)

        # CASE select_related
        pizza = await Pizza.aobjects.select_related("price").get(id=1)
        self.assertEqual(pizza.price.amount, Decimal("9.99"))

        # CASE prefetch_related
        box = await Box.aobjects.prefetch_related("pizza_set").get(id=1)
        self.assertEqual(box.pizza_set.all()[0].name, "Thicc Pizza")

    @async_to_sync
    async def test_magic_methods(self):
        # CASE slicing
        prices_count = await Price.aobjects.all()[:2].count()
        self.assertEqual(prices_count, 2)
        prices_count = await Price.aobjects.all()[1:2].count()
        self.assertEqual(prices_count, 1)
        price_med = await Price.aobjects.order_by("amount")[1:].first()
        self.assertEqual(price_med.amount, Decimal("29.99"))

        # CASE getitem
        price_med = await Price.aobjects.order_by("amount")[1:2][0]
        self.assertEqual(price_med.amount, Decimal("29.99"))
        prices_highest = await Price.aobjects.order_by("-amount")[:2][0]
        self.assertEqual(prices_highest.amount, Decimal("39.99"))
        prices_lowest = await Price.aobjects.order_by("-amount")[-1]
        self.assertEqual(prices_lowest.amount, Decimal("9.99"))

        # CASE len
        try:
            len(Price.aobjects.all())
            self.fail("This should not work")
        except NotImplementedError:
            pass

        # CASE bool
        try:
            bool(Price.aobjects.all())
            self.fail("This should not work")
        except NotImplementedError:
            pass

        # CASE repr
        self.assertIsInstance(repr(Price.aobjects.all()), str)

        # CASE str
        self.assertIsInstance(str(Price.aobjects.all()), str)

    @async_to_sync
    async def test_operator_methods(self):
        # CASE or (|)
        qa = Price.aobjects.filter(currency="usd")
        qb = Price.aobjects.filter(currency="eur")
        all_prices = await (qa | qb).eval()
        for price in all_prices:
            self.assertIn(price.currency, ["usd", "eur"])
        async for price in qa | qb:
            self.assertIn(price.currency, ["usd", "eur"])

        # CASE and (&)
        qa = Price.aobjects.filter(amount__gt=Decimal("2.99"))
        qb = Price.aobjects.filter(amount__gt=Decimal("19.99"))
        gt_20_prices = await (qa & qb).eval()
        for price in gt_20_prices:
            self.assertGreater(price.amount, Decimal("19.99"))
        async for price in qa & qb:
            self.assertGreater(price.amount, Decimal("19.99"))

    @async_to_sync
    async def test_foreign_access(self):
        # NOTE: DOES NOT RELY ON select_related NOR prefect_related
        price = await Price.aobjects.get(id=1)
        big_price = await Price.aobjects.get(id=2)
        eur_price = await Price.aobjects.get(id=3)
        pizza = await Pizza.aobjects.get(id=1)
        weird_pizza = await Pizza.aobjects.create(id=2, name="Weird Pizza", price=big_price)
        bacon = await Topping.aobjects.get(id=1)
        mushroom = await Topping.aobjects.get(id=2)
        random = await Topping.aobjects.get(id=3)
        medium_box = await Box.aobjects.get(id=1)

        # CASE one-to-one rel
        self.assertEqual(await pizza.aprice, price)
        self.assertEqual(await price.apizza, pizza)

        # CASE many-to-one rel
        self.assertEqual(await pizza.abox, medium_box)
        self.assertEqual(await medium_box.apizza_set.all().get(id=1), pizza)
        await medium_box.apizza_set.add(weird_pizza) # reverse add
        self.assertEqual(await medium_box.apizza_set.all().get(id=2), weird_pizza)
        weird_pizza = await Pizza.aobjects.get(id=2)
        self.assertEqual(await weird_pizza.abox, medium_box)
        await medium_box.apizza_set.remove(weird_pizza) # reverse remove
        weird_pizza = await Pizza.aobjects.get(id=2)
        self.assertEqual(await weird_pizza.abox, None)
        await medium_box.apizza_set.set([weird_pizza]) # reverse set
        pizza = await Pizza.aobjects.get(id=1)
        weird_pizza = await Pizza.aobjects.get(id=2)
        self.assertEqual(await pizza.abox, None)
        self.assertEqual(await weird_pizza.abox, medium_box)
        await medium_box.apizza_set.clear() # reverse clear
        pizza = await Pizza.aobjects.get(id=1)
        weird_pizza = await Pizza.aobjects.get(id=2)
        self.assertEqual(await pizza.abox, None)
        self.assertEqual(await weird_pizza.abox, None)
        pizza.box = medium_box
        await pizza.asave()
        self.assertEqual(await medium_box.apizza_set.all().first(), pizza)

        # CASE many-to-many forward rel
        self.assertEqual(await pizza.atoppings.all().exists(), False)
        await pizza.atoppings.add(bacon, mushroom) # forward add
        self.assertEqual(await bacon.apizza_set.get(id=1), pizza)
        self.assertEqual(await mushroom.apizza_set.get(id=1), pizza)
        await pizza.atoppings.remove(bacon) # forward remove
        self.assertEqual(await bacon.apizza_set.filter(id=1).exists(), False)
        self.assertEqual(await mushroom.apizza_set.get(id=1), pizza)
        await pizza.atoppings.set([mushroom, random]) # forward set
        self.assertEqual(await bacon.apizza_set.filter(id=1).exists(), False)
        self.assertEqual(await mushroom.apizza_set.get(id=1), pizza)
        self.assertEqual(await random.apizza_set.get(id=1), pizza)
        await pizza.atoppings.clear() # forward clear
        self.assertEqual(await bacon.apizza_set.filter(id=1).exists(), False)
        self.assertEqual(await mushroom.apizza_set.filter(id=1).exists(), False)
        self.assertEqual(await random.apizza_set.filter(id=1).exists(), False)
        self.assertEqual(await pizza.atoppings.all().count(), 0)

        # CASE many-to-many reverse rel
        self.assertEqual(await mushroom.apizza_set.all().exists(), False)
        await mushroom.apizza_set.add(pizza) # reverse add
        self.assertEqual(await pizza.atoppings.filter(id=2).exists(), True)
        self.assertEqual(await pizza.atoppings.all().count(), 1)
        await mushroom.apizza_set.remove(pizza) # reverse remove
        self.assertEqual(await pizza.atoppings.filter(id=2).exists(), False)
        self.assertEqual(await pizza.atoppings.all().count(), 0)
        await mushroom.apizza_set.set([pizza, weird_pizza]) # reverse set
        self.assertEqual(await pizza.atoppings.filter(id=2).exists(), True)
        self.assertEqual(await pizza.atoppings.all().count(), 1)
        self.assertEqual(await weird_pizza.atoppings.filter(id=2).exists(), True)
        self.assertEqual(await weird_pizza.atoppings.all().count(), 1)
        await mushroom.apizza_set.clear() # reverse set
        self.assertEqual(await pizza.atoppings.filter(id=2).exists(), False)
        self.assertEqual(await pizza.atoppings.all().count(), 0)
        self.assertEqual(await weird_pizza.atoppings.filter(id=2).exists(), False)
        self.assertEqual(await weird_pizza.atoppings.all().count(), 0)

        # NOTE: THERE ARE UNCOVERED TEST CASES PENDING TO BE ADDED.
