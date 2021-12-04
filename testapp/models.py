from django.db import models

from asgimod.mixins import AsyncMixin
from asgimod.db import AsyncManyToManyRelatedManager


class Topping(AsyncMixin, models.Model):
    name = models.CharField(max_length=30)
    apizza_set: AsyncManyToManyRelatedManager["Pizza"]


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
