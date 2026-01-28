from django.contrib import admin

from reusable.admins import ReadOnlyAdminDateFieldsMIXIN
from . import models


@admin.register(models.Notification)
class NotificationAdmin(ReadOnlyAdminDateFieldsMIXIN):
    raw_id_fields = ("transaction",)
    readonly_fields = ("last_sent",)
    ordering = ("-last_sent",)
    list_display = (
        "pk",
        "coin",
        "transaction",
        "get_price",
        "percentage",
        "market",
        "profile",
        "channel",
        "status",
        "last_sent",
        "interval",
        "updated_at",
    )
    list_filter = ("coin",)

    @admin.display(description="price")
    def get_price(self, instance):
        """
        Return the price of the notification in a formatted way.
        """
        if instance.price:
            return f"{float(instance.price):,}"
        return None
