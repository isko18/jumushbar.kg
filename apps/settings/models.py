from django.db import models
from ckeditor.fields import RichTextField

class PrivacyPolicy(models.Model):
    content = RichTextField(verbose_name="HTML-содержимое политики конфиденциальности")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Политика конфиденциальности"
        verbose_name_plural = "Политики конфиденциальности"

    def __str__(self):
        return "Политика конфиденциальности"


class PublicOffer(models.Model):
    content = RichTextField(verbose_name="HTML-содержимое публичной оферты")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Публичная оферта"
        verbose_name_plural = "Публичные оферты"

    def __str__(self):
        return "Публичная оферта"


class RefundPolicy(models.Model):
    content = RichTextField(verbose_name="HTML-содержимое политики возврата")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Политика возврата"
        verbose_name_plural = "Политики возврата"

    def __str__(self):
        return "Политика возврата"


class CardPaymentTerms(models.Model):
    content = RichTextField(verbose_name="HTML-содержимое условий оплаты картой")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Условия оплаты картой"
        verbose_name_plural = "Условия оплаты картой"

    def __str__(self):
        return "Условия оплаты картой"
