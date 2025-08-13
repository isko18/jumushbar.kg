from django.db import models
from apps.orders.models import Order
from apps.users.models import User

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('success', 'Успешно'),
        ('failed', 'Неудача'),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        verbose_name="Заказ"
    )
    executor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Исполнитель"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ID платежа"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    def __str__(self):
        return f"Payment #{self.pk} — {self.status}"

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
