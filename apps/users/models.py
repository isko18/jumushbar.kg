from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.files.base import ContentFile
from apps.utils import convert_imagefile_to_webp

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class UserRegion(models.Model):
    title = models.CharField(max_length=155)

    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'

class UserSubRegion(models.Model):
    title = models.CharField(max_length=155)
    region = models.ForeignKey(UserRegion, on_delete=models.CASCADE, related_name='subregions')

    class Meta:
        verbose_name = 'Подрегион'
        verbose_name_plural = 'Подрегионы'

class Profession(models.Model):
    title = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Профессия'
        verbose_name_plural = 'Профессии'

class User(AbstractUser, PermissionsMixin):
    ROLE = (
        ("Заказчик", "Заказчик"),
        ("Исполнитель", "Исполнитель")
    )
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=155)
    phone = models.CharField(max_length=20)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(null=True, blank=True, choices=ROLE, max_length=15, verbose_name='Роли')
    profession = models.ForeignKey(Profession, null=True, blank=True, on_delete=models.SET_NULL)
    subregion = models.ForeignKey(UserSubRegion, null=True, blank=True, on_delete=models.SET_NULL)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    passport_front = models.ImageField(upload_to='passport/front/', null=True, blank=True)
    passport_back = models.ImageField(upload_to='passport/back/', null=True, blank=True)
    passport_selfie = models.ImageField(upload_to='passport/selfie/', null=True, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='KGS')
    is_blocked = models.BooleanField(default=False)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def save(self, *args, **kwargs):
        self.passport_front = self._process_image_field(self.passport_front)
        self.passport_back = self._process_image_field(self.passport_back)
        self.passport_selfie = self._process_image_field(self.passport_selfie)
        super().save(*args, **kwargs)

    def _process_image_field(self, image_field):
        if image_field and not image_field.name.endswith('.webp'):
            webp_content = convert_imagefile_to_webp(image_field)
            filename = f"{image_field.name.split('.')[0]}.webp"
            return ContentFile(webp_content, filename)
        return image_field
        
    @property
    def average_rating(self):
        from django.db.models import Avg
        return self.reviews.aggregate(avg=Avg('rating'))['avg'] or 0