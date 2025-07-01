import logging
from decimal import Decimal

from django.core.cache import cache
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Coin, Transaction
from .serializers import TransactionSerializer, CachedPricesSerializer, CoinSerializer

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def format_number(value):
    """
    Format a number to remove trailing zeros.
    If it's a whole number, return an integer, otherwise return a float.
    """
    # Convert to Decimal for precise handling
    if isinstance(value, float) or isinstance(value, int) or isinstance(value, str):
        value = Decimal(str(value))

    # Check if it's a whole number
    if value % 1 == 0:
        return int(value)
    return float(
        str(value).rstrip("0").rstrip(".") if "." in str(value) else str(value)
    )


class CachedPricesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing cached cryptocurrency prices.
    Returns a list of objects with code, title, icon, and price fields.
    """

    serializer_class = CachedPricesSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Coin.objects.filter(enable=True)

    def list(self, request, *args, **kwargs):
        """
        Override the list method to return cached prices instead of model data.
        """
        all_prices = []

        # Get all coins from the database
        coins = self.get_queryset()
        logger.info(f"Found {coins.count()} coins in database")

        # Check for cached prices for each coin
        for coin in coins:
            logger.info(f"Checking prices for coin: {coin.code}")
            price = None

            # Check for direct coin price (format used by Bitpin.cache_all_prices)
            key = f"coin_{coin.code}".lower()
            price = cache.get(key)
            logger.info(f"Checking key: {key}, found price: {price}")

            if not price:
                # If not found,
                # check for market-specific keys
                # (format used by update_bitpin_prices task)
                for market in ["irt", "usdt"]:
                    key = f"coin_{coin.code}_{market}".lower()
                    price = cache.get(key)
                    logger.info(f"Checking market key: {key}, found price: {price}")

                    if price:
                        break

            icon_svg_url = (
                request.build_absolute_uri(coin.icon.url) if coin.icon else None
            )
            icon_png_url = (
                request.build_absolute_uri(coin.icon_png.url) if coin.icon_png else None
            )
            # Create coin data object
            coin_data = {
                "code": coin.code,
                "title": coin.title
                or coin.code,  # Use code as fallback if title is None
                "icon": icon_png_url if icon_png_url else icon_svg_url,
                "price": format_number(price) if price else None,
            }

            all_prices.append(coin_data)
            logger.info(f"Added coin data: {coin_data}")

        # If no prices found, try to get any cached values for debugging
        if not any(coin["price"] for coin in all_prices):
            logger.warning(
                "No prices found in cache. Checking for any cached values..."
            )
            # Try to get a sample of cached values to see what's in there
            sample_keys = [
                "coin_btc",
                "coin_eth",
                "coin_btc_irt",
                "coin_btc_usdt",
                "coin_eth_irt",
                "coin_eth_usdt",
            ]
            for key in sample_keys:
                value = cache.get(key)
                logger.info(f"Sample key {key}: {value}")

        logger.info(f"Final prices count: {len(all_prices)}")

        # Sort coins by price in descending order
        # Handle None prices by putting them at the end
        all_prices.sort(
            key=lambda x: (
                x["price"] is None,
                -float(x["price"]) if x["price"] is not None else 0,
            )
        )

        # Apply pagination
        page = self.paginate_queryset(all_prices)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # If pagination is not applied, return all data
        serializer = self.get_serializer(all_prices, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing transactions.
    Supports filtering by coin using query parameters:
    - coin: Filter by coin ID
    - coin__code: Filter by coin code (e.g., BTC, ETH)
    """

    serializer_class = TransactionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["coin", "coin__code"]
    ordering_fields = ["jdate", "amount", "price"]
    ordering = ["-jdate"]

    def get_queryset(self):
        return Transaction.objects.all().select_related("coin").order_by("-jdate")


class CoinViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only viewset for viewing coins.
    Provides list and detail views for coins.
    """

    queryset = Coin.objects.filter(enable=True).order_by("code")
    serializer_class = CoinSerializer
    pagination_class = StandardResultsSetPagination
