from django_filters import FilterSet, DateFilter

from .models import Transaction


class TransactionFilter(FilterSet):
    """
    Custom filter for Transaction model.
    Supports date range filtering with date_from and date_to parameters.
    """

    date_from = DateFilter(field_name="jdate", lookup_expr="gte")
    date_to = DateFilter(field_name="jdate", lookup_expr="lte")

    class Meta:
        model = Transaction
        fields = ["coin", "coin__code", "date_from", "date_to"]
