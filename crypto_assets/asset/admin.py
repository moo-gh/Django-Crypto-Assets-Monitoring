from django.contrib import admin

from reusable.admins import ReadOnlyAdminDateFieldsMIXIN
from . import models


@admin.register(models.Asset)
class AssetAdmin(ReadOnlyAdminDateFieldsMIXIN):
    readonly_fields = ("quantity", "value")
    list_display = (
        "pk",
        "profile",
        "coin",
        "quantity",
        "get_value",
    )
    list_filter = ("coin",)

    @admin.display(description="value")
    def get_value(self, instance):
        if instance.value:
            return f"{float(instance.value):,}"
        return None
