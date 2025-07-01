from rest_framework import serializers

from .models import Transaction, Coin


class CoinSerializer(serializers.ModelSerializer):
    """
    Serializer for Coin model.
    Read-only serializer that includes all relevant coin information.
    """

    icon_url = serializers.SerializerMethodField()
    icon_png_url = serializers.SerializerMethodField()

    class Meta:
        model = Coin
        fields = [
            "id",
            "title",
            "code",
            "icon_url",
            "icon_png_url",
            "icon_background_color",
            "market",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_icon_url(self, obj):
        if obj.icon:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url
        return None

    def get_icon_png_url(self, obj):
        if obj.icon_png:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.icon_png.url)
        return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["icon_url"] = ret["icon_png_url"] or ret["icon_url"]
        return ret


class CachedPricesSerializer(serializers.Serializer):
    """
    Serializer for cached cryptocurrency prices.
    Returns a list of objects with code, title, icon, and price fields.
    """

    code = serializers.CharField()
    title = serializers.CharField()
    icon = serializers.CharField(allow_null=True)
    price = serializers.FloatField(allow_null=True)


class TransactionSerializer(serializers.ModelSerializer):
    coin = serializers.CharField(source="coin.code", read_only=True)
    current_value = serializers.FloatField(source="get_current_value", read_only=True)
    change_percentage = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "market",
            "coin",
            "price",
            "quantity",
            "total_price",
            "current_value",
            "date",
            "change_percentage",
        ]
        read_only_fields = fields

    def get_change_percentage(self, obj):
        if obj.type == Transaction.BUY:
            return obj.get_change_percentage
        return None

    def get_date(self, obj):
        if obj.jdate:
            return obj.jdate.strftime("%Y-%m-%d")
        return None

    def to_representation(self, instance):
        from .views import format_number

        ret = super().to_representation(instance)

        # Format numeric fields
        for field in [
            "price",
            "quantity",
            "total_price",
            "current_value",
            "change_percentage",
        ]:
            if ret[field] is not None:
                ret[field] = format_number(ret[field])

        return ret
