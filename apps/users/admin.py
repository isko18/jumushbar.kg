from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserRegion, UserSubRegion, Profession

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('username', 'email', 'full_name', 'is_verified', 'role', 'is_staff')
    list_filter = ('is_verified', 'role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'full_name', 'phone')
    ordering = ('-date_joined',)
    filter_horizontal = ('professions',)  # отображение M2M удобно

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Личная информация', {
            'fields': ('full_name', 'phone', 'role', 'professions', 'subregion', 'balance')
        }),
        ('Паспортные данные', {
            'fields': ('passport_front', 'passport_back', 'passport_selfie')
        }),
        ('Подтверждение', {
            'fields': ('is_verified', 'email_verification_code')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Даты', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'is_verified', 'is_staff', 'is_superuser'
            )
        }),
    )


@admin.register(UserRegion)
class UserRegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)


@admin.register(UserSubRegion)
class UserSubRegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'region')
    search_fields = ('title',)
    list_filter = ('region',)


@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)
