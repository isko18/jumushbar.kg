from django.db import models
from ckeditor.fields import RichTextField

class PrivacyPolicy(models.Model):
    content = RichTextField(verbose_name="HTML-содержимое")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Политика конфиденциальности"

class PublicOffer(models.Model):
    content = RichTextField(verbose_name="HTML-содержимое")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Публичная оферта"

class RefundPolicy(models.Model):
    content = RichTextField(verbose_name="HTML-содержимое")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Политика возврата"

class CardPaymentTerms(models.Model):
    content = RichTextField(verbose_name="HTML-содержимое")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Оплата банковской картой"
