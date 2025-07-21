from django.db import models
from django.core.files.base import ContentFile
from apps.utils import convert_imagefile_to_webp
from apps.users.models import User, UserSubRegion, Profession

class Category(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categories', blank=True, null=True)
    profession = models.ForeignKey(Profession, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.title


class Order(models.Model):
    STATUS_CHOICES = (
        ('active', 'Активный'),
        ('completed', 'Завершённый'),
        ('cancelled', 'Отменённый'),
    )

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_negotiable = models.BooleanField(default=False)
    deadline = models.DateField()
    preferred_time = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    subregion = models.ForeignKey(UserSubRegion, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']  # ← новая строка

    def __str__(self):
        return f"Заказ #{self.pk} от {self.customer}"


class OrderPhoto(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='orders/photos/')

    def save(self, *args, **kwargs):
        if self.image and not self.image.name.endswith('.webp'):
            webp_content = convert_imagefile_to_webp(self.image)
            filename = f"{self.image.name.split('.')[0]}.webp"
            self.image.save(filename, ContentFile(webp_content), save=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Фото заказа"
        verbose_name_plural = "Фото заказов"

class OrderResponse(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='responses')
    executor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_responses')
    responded_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('order', 'executor')
        verbose_name = "Отклик"
        verbose_name_plural = "Отклики"

class OrderRespondLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    executor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    idempotency_key = models.CharField(max_length=100, blank=True, null=True)
    success = models.BooleanField()
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    executor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    rating = models.PositiveSmallIntegerField()  # от 1 до 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"Отзыв {self.rating}★ от {self.customer} исполнителю {self.executor}"