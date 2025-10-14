import logging

from django.core.cache import cache
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Coin, Transaction
from .serializers import TransactionSerializer, CachedPricesSerializer, CoinSerializer
from .utils import format_number

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


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

    def list(self, request, *args, **kwargs):
        """
        Override list method to include total profit/loss when filtering by coin.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Check if filtering by coin
        coin_id = request.query_params.get("coin")
        coin_code = request.query_params.get("coin__code")

        # Calculate total profit/loss if coin is specified
        coin_stats = None
        if coin_id or coin_code:
            from .models import TransactionTypeChoices

            # Filter BUY transactions only for profit/loss calculation
            buy_transactions = queryset.filter(type=TransactionTypeChoices.BUY)

            total_profit_loss = 0
            coin_obj = None
            market = None

            for transaction in buy_transactions:
                profit_loss = transaction.get_current_value - transaction.total_price
                total_profit_loss += profit_loss

                # Get coin and market from first transaction
                if coin_obj is None:
                    coin_obj = transaction.coin
                    market = transaction.market

            # If no buy transactions, get coin from any transaction
            if coin_obj is None and queryset.exists():
                first_transaction = queryset.first()
                coin_obj = first_transaction.coin
                market = first_transaction.market

            # Get current price if we have a coin
            current_price = None
            if coin_obj and market:
                try:
                    current_price = coin_obj.price(market)
                except Exception as e:
                    logger.error(f"Error getting price for coin {coin_obj.code}: {e}")

            coin_stats = {
                "total_profit_loss": format_number(total_profit_loss),
                "current_price": format_number(current_price)
                if current_price
                else None,
            }

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data)

            # Add coin stats to response if available
            if coin_stats:
                response_data.data["coin_stats"] = coin_stats

            return response_data

        # If pagination is not applied
        serializer = self.get_serializer(queryset, many=True)
        response_data = {"results": serializer.data}

        # Add coin stats to response if available
        if coin_stats:
            response_data["coin_stats"] = coin_stats

        return Response(response_data)


class CoinViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only viewset for viewing coins.
    Provides list and detail views for coins.
    """

    queryset = Coin.objects.filter(enable=True).order_by("code")
    serializer_class = CoinSerializer
    pagination_class = StandardResultsSetPagination
