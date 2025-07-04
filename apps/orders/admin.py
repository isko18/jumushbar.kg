from django.contrib import admin
from apps.orders.models import Category, Order, OrderPhoto
# Register your models here.
admin.site.register(Category)
admin.site.register(Order)
admin.site.register(OrderPhoto)