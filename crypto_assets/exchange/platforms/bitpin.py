import json
import logging
from decimal import Decimal
import requests
from requests.exceptions import ReadTimeout, HTTPError, RequestException

from django.core.cache import cache
from django.conf import settings

from exchange.platforms.base import BaseExchange


logger = logging.getLogger(__name__)


class Bitpin(BaseExchange):
    def __init__(self):
        self.api_addr = "https://api.bitpin.ir/v1/mkt/markets/"
        self.price_round = 5
        self.cache_price_ttl = settings.BITPIN_PRICE_CACHE_TTL

    def get_price(self, coin, market: str) -> Decimal:
        coin_key = f"coin_{coin.code}_{market}".lower()
        cache_price = cache.get(coin_key)
        if cache_price:
            return cache_price
        return 0

    def call_coins_api(self) -> list[dict]:
        resp = None
        try:
            resp = requests.get(self.api_addr, timeout=10)
            coins = resp.json()["results"]

        except (TimeoutError, ReadTimeout) as e:
            error = f"TimeoutError in getting prices from bitpin: {e}"
            logger.warning(error)
            return []

        except HTTPError as e:
            error = f"HTTPError in getting prices from Bitpin: {e}"
            if resp:
                error += f"\n\nresponse code: {resp.status_code}"
            logger.warning(error)
            return []

        except json.JSONDecodeError as e:
            error = f"JSONDecodeError in getting prices from bitpin: {e}"
            error += f"\n\nresponse: {resp}"
            if resp:
                error += f"\n\nresponse code: {resp.status_code}"
            logger.warning(error)
            return []

        except RequestException as e:
            error = f"RequestException in getting prices from Bitpin: {e}"
            if resp:
                error += f"\n\nresponse code: {resp.status_code}"
            logger.warning(error)
            return []

        # otherwise, log as an error
        except Exception as e:
            error = f"Error in getting prices from bitpin: {e}"
            error += f"\n\nresponse: {resp}"
            if resp:
                error += f"\n\nresponse code: {resp.status_code}"
            logger.error(error)
            return []

        return coins

    def cache_all_prices(self, req_coins: list[str] = []):
        coins = self.call_coins_api()
        for coin in coins:
            coin_code = coin["code"].lower()
            if req_coins and coin_code not in req_coins:
                continue
            key = f"coin_{coin_code}".lower()
            price = round(Decimal(coin["price"]), self.price_round)
            cache.set(key, price, self.cache_price_ttl)
