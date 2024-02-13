from django.db import models

from accounts.models import Owner


class ProductType(models.Model):
    name = models.CharField(max_length=128, unique=True, verbose_name="Название")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип продукции"
        verbose_name_plural = "Типы продукции"


class Product(models.Model):
    product_type = models.ForeignKey(ProductType, related_name="products", on_delete=models.PROTECT,
                                     verbose_name="Тип продукции")
    name = models.CharField(max_length=128, unique=True, verbose_name="Название")
    price = models.FloatField(verbose_name="Цена")

    def __str__(self):
        return f"{self.name}: {self.price} руб."

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукция"


class SpecialPrice(models.Model):
    owner = models.ForeignKey(Owner, related_name="special_prices", on_delete=models.CASCADE, verbose_name="Владелец")
    product = models.ForeignKey(Product, related_name="special_prices", on_delete=models.CASCADE,
                                verbose_name="Продукт")
    price = models.FloatField(verbose_name="Цена")

    def __str__(self):
        return f"{self.product} ({self.owner.fio})"

    class Meta:
        verbose_name = "Специальная цена"
        verbose_name_plural = "Специальные цены"