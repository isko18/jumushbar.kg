import django_filters
from apps.orders.models import Order

class OrderFilter(django_filters.FilterSet):
    budget_min = django_filters.NumberFilter(field_name='budget', lookup_expr='gte')
    budget_max = django_filters.NumberFilter(field_name='budget', lookup_expr='lte')
    is_negotiable = django_filters.BooleanFilter(field_name='is_negotiable')
    category = django_filters.NumberFilter(field_name='category_id')
    subregion = django_filters.NumberFilter(field_name='subregion_id')
    region = django_filters.CharFilter(field_name='location', lookup_expr='icontains')

    deadline_day = django_filters.NumberFilter(method='filter_by_day')
    deadline_month = django_filters.NumberFilter(method='filter_by_month')
    deadline_year = django_filters.NumberFilter(method='filter_by_year')

    class Meta:
        model = Order
        fields = []

    def filter_by_day(self, queryset, name, value):
        return queryset.filter(deadline__day=value)

    def filter_by_month(self, queryset, name, value):
        return queryset.filter(deadline__month=value)

    def filter_by_year(self, queryset, name, value):
        return queryset.filter(deadline__year=value)
