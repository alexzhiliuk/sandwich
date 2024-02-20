from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import Owner, Employee, Point


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

    def get_special_price_for_user(self, owner):
        special_price = SpecialPrice.objects.filter(product=self, owner=owner).first()
        return special_price

    def generate_message(self, owner):
        special_price = self.get_special_price_for_user(owner)
        if special_price:
            return f"<b>{self.name}</b>\n{special_price.price} руб."
        return f"<b>{self.name}</b>\n{self.price} руб."


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

    class Status(models.TextChoices):
        CREATED = "CR", "Создан"
        ACCEPTED = "AC", "Принят"
        COMPLETED = "CO", "Завершен"

    owner = models.ForeignKey(Owner, related_name="orders", on_delete=models.CASCADE, verbose_name="Владелец")
    employee = models.ForeignKey(Employee, related_name="orders", on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Сотрудник")
    point = models.ForeignKey(Point, related_name="orders", on_delete=models.SET_NULL, null=True, verbose_name="Точка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    pickup = models.BooleanField(default=False, verbose_name="Самовывоз")
    status = models.CharField(max_length=32, default=Status.CREATED, choices=Status.choices, verbose_name="Статус")

    def __str__(self):
        if self.employee:
            return f"{self.employee}: {self.created_at}"
        return f"{self.owner}: {self.created_at}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def clean(self):
        super().clean()
        if self.employee:
            if self.employee.owner != self.owner:
                raise ValidationError('Сотрудник не принадлежит к данному владельцу!')

    def get_final_info(self):
        count = 0
        price = 0
        for item in self.items.all():
            count += 1
            price += item.price
        return count, price

    def fill(self, ordered_items):
        for product, count in ordered_items.items():
            OrderItem.objects.create(order=self, product=product, count=count)

    def update_item(self, product, count):
        item = self.items.filter(product=product).first()
        if item:
            item.count = count
            item.save()
        else:
            OrderItem.objects.create(order=self, product=product, count=count)

    def delete_item(self, product):
        item = self.items.filter(product=product).first()
        if item:
            item.delete()

    def get_details(self):
        details = ""
        total_count = 0
        total_price = 0
        for item in self.items.all():
            item_price = item.price
            item_count = item.count
            total_price += item_price
            total_count += item_count
            details += f"{item.product.name} {item_count} шт. {item_price} руб.\n"
        details += f"-----\nВсего товаров: {total_count} шт.\nИтоговая сумма: {total_price} руб."
        return details

    def generate_message(self):
        if self.pickup:
            order_delivery = "Самовывоз"
        else:
            order_delivery = self.point.address
        message = f"Заказ:\n<i>{self.created_at.date().strftime('%Y-%m-%d')}</i>\n<b>{order_delivery}</b>\n-----\n"
        message += self.get_details()

        return message


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

    def get_special_price_for_product(self):
        owner = self.order.owner
        return self.product.get_special_price_for_user(owner)

    @property
    def price(self):
        special_price = self.get_special_price_for_product()

        if special_price:
            return round(special_price.price * self.count, 2)

        return round(self.product.price * self.count, 2)
