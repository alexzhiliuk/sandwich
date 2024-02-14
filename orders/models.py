from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import Owner, Employee


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


class Order(models.Model):
    owner = models.ForeignKey(Owner, related_name="orders", on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name="Владелец")
    employee = models.ForeignKey(Employee, related_name="orders", on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Сотрудник")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    pickup = models.BooleanField(default=False, verbose_name="Самовыоз")

    def __str__(self):
        if self.owner:
            return f"{self.owner}: {self.created_at}"
        return f"{self.employee}: {self.created_at}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def clean(self):
        super().clean()
        if self.owner and self.employee or not self.owner and not self.owner:
            raise ValidationError('Обязательно должен существовать сотрудник либо владелец, но не одновременно')

    def get_final_info(self):
        count = 0
        price = 0
        for item in self.items.all():
            count += 1
            price += item.price
        return count, price


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(Product, related_name="ordered_items", on_delete=models.CASCADE, verbose_name="Продукт")
    count = models.PositiveIntegerField(verbose_name="Количество")

    def __str__(self):
        return f"{self.product} Кол-во: {self.count} шт."

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказов"
        unique_together = [["order", "product"]]

    @property
    def price(self):
        owner = self.order.owner or self.order.employee.owner
        special_price = SpecialPrice.objects.filter(product=self.product, owner=owner).first()

        if special_price:
            return special_price.price * self.count

        return self.product.price * self.count