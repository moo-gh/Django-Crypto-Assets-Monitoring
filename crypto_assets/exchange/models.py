from django.db import models, transaction
from django.utils.functional import cached_property
from django_jalali.db import models as jmodels

from user.models import Profile
from reusable.models import BaseModel
from . import tasks
from .platforms.bitpin import Bitpin
from .platforms.wallex import Wallex


class ExchangeNameChoices(models.TextChoices):
    WALLEX = "wallex", "wallex"
    BITPIN = "bitpin", "bitpin"


class MarketChoices(models.TextChoices):
    TOMAN = "irt", "irt"
    TETHER = "usdt", "usdt"


class Exchange(BaseModel):
    name = models.CharField(max_length=100, choices=ExchangeNameChoices.choices)

    def __str__(self):
        return f"({self.pk} - {self.name})"

    def get_platform(self):
        if self.name == ExchangeNameChoices.WALLEX:
            return Wallex()
        if self.name == ExchangeNameChoices.BITPIN:
            return Bitpin()
        raise Exception("Exchange name is not valid")

    def price(self, coin, market):
        return self.get_platform().get_price(coin, market)

    def cache_all_prices(self):
        return self.get_platform().cache_all_prices()


class Coin(BaseModel):
    title = models.CharField(max_length=100, unique=True, null=True)
    code = models.CharField(max_length=20, unique=True)
    enable = models.BooleanField(default=True)
    icon = models.FileField(
        upload_to="coin_logos/",
        blank=True,
        null=True,
        help_text="SVG icon for the coin",
    )
    icon_png = models.FileField(
        upload_to="coin_logos/",
        blank=True,
        null=True,
        help_text="PNG icon for the coin",
    )
    icon_background_color = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Background color for SVG icons in hex format (e.g. #FFFFFF)",
    )

    market = models.CharField(
        max_length=10, choices=MarketChoices.choices, null=True, blank=True
    )

    def __str__(self):
        return f"({self.pk} - {self.code})"

    def get_price(self, market):
        return f"{float(self.price(market)):,}"

    def price(self, market):
        exchange = Exchange.objects.last()
        return exchange.price(self, market)


class Transaction(BaseModel):
    BUY = "buy"
    SELL = "sell"
    TYPE_CHOICES = ((BUY, BUY), (SELL, SELL))
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    jdate = jmodels.jDateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=20, decimal_places=10)
    quantity = models.DecimalField(max_digits=20, decimal_places=10)
    market = models.CharField(
        max_length=10, choices=MarketChoices.choices, null=True, blank=True
    )
    coin = models.ForeignKey(
        Coin, related_name="transactions", on_delete=models.CASCADE
    )
    profile = models.ForeignKey(
        Profile, related_name="transactions", on_delete=models.CASCADE
    )
    change = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    platform_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self) -> str:
        return f"({self.pk} - {self.type} - {self.coin})"

    @property
    def total_price(self):
        return int(self.price * self.quantity)

    @cached_property
    def get_current_value(self):
        return int(self.current_price * self.quantity)

    @cached_property
    def current_price(self):
        return self.coin.price(self.market) or 0

    @property
    def get_price(self):
        if self.market == MarketChoices.TOMAN:
            return f"{int(self.price):,}"
        return float(round(self.price, 2))

    @cached_property
    def get_current_price(self):
        if self.market == MarketChoices.TOMAN:
            return f"{int(self.current_price):,}"
        return float(round(self.current_price, 2))

    @property
    def get_quantity(self):
        return float(round(self.quantity, 6))

    @property
    def get_profit_or_loss(self):
        if self.type == Transaction.SELL:
            return "-"
        return f"{int(self.get_current_value - self.total_price):,}"

    @cached_property
    def get_total_price(self):
        return f"{self.total_price:,}"

    @property
    def get_current_value_admin(self):
        return f"{self.get_current_value:,}"

    @property
    def construct_platform_id(self):
        platform_id_components = [
            str(self.jdate),
            self.coin.code,
            self.market,
            self.type,
            str(float(self.quantity)),
            str(float(self.price)),
        ]
        return "|".join(platform_id_components).lower()

    @cached_property
    def get_change_percentage(self):
        if self.type == Transaction.SELL:
            return "-"
        # shows the percentage of profit or loss
        if self.total_price == 0:
            return 0
        return round(
            ((self.get_current_value - self.total_price) / self.total_price) * 100, 2
        )


class Importer(BaseModel):
    file = models.FileField(upload_to="importer")
    profile = models.ForeignKey(
        Profile, related_name="importers", on_delete=models.CASCADE
    )
    success_count = models.IntegerField(default=0)
    fail_count = models.IntegerField(default=0)
    errors = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"({self.pk} - {self.file})"

    def process(self):
        print("process importer")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            transaction.on_commit(lambda: tasks.process_importer.delay(self.pk))
            super().save(*args, **kwargs)
