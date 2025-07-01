import csv
from decimal import Decimal
from datetime import datetime

from jdatetime import JalaliToGregorian
from celery import shared_task
from celery.utils.log import get_task_logger

from crypto_assets.celery import app
from .platforms.bitpin import Bitpin
from . import models

logger = get_task_logger(__name__)


def get_georgina(jdate: str):
    persian_time = jdate.split("-")[0].strip()
    persian_date = jdate.split("-")[1].strip()
    # Split the date and time strings into components
    date_components = list(map(int, persian_date.split("/")))
    time_components = list(map(int, persian_time.split(":")))

    # Convert Persian date to Gregorian date
    gregorian_date = JalaliToGregorian(*date_components)
    gregorian_datetime = datetime(
        gregorian_date.gyear,
        gregorian_date.gmonth,
        gregorian_date.gday,
        time_components[0],
        time_components[1],
    )

    return gregorian_datetime


@app.task(name="update_bitpin_prices")
def update_bitpin_prices():
    logger.info("Updating Bitpin prices started at %s", datetime.now())
    bitpin = Bitpin()
    coins = models.Coin.objects.all()
    coins_codes = []
    for coin in coins:
        coins_codes.append(f"{coin.code}_irt".lower())
        coins_codes.append(f"{coin.code}_usdt".lower())
    bitpin.cache_all_prices(coins_codes)
    logger.info("Updating Bitpin prices finished at %s", datetime.now())


@shared_task
def process_importer(importer_id):
    success_counter = 0
    fail_counter = 0
    importer = models.Importer.objects.get(pk=importer_id)
    errors = importer.errors or ""
    with open(importer.file.path, "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        # if "mode" in the header row.low(), it's new format
        # otherwise, it's old format
        header = next(csv_reader)
        header = [h.lower() for h in header]
        new_format = False
        if "mode" in header:
            new_format = True

        for row in csv_reader:
            try:
                if new_format:
                    (
                        date,
                        market,
                        trade_type,
                        _mode,
                        amount,
                        _total,
                        price,
                        _price_limit,
                        _price_stop,
                        _price_limit_oco,
                        _fulfilled,
                    ) = row
                else:
                    date, market, trade_type, amount, _total, price, _fee = row
            except Exception as e:
                print(e)

            date = get_georgina(date)
            title = market.split("/")[0].lower()
            market = market.split("/")[1].lower()
            if market == "toman":
                market = "irt"
            if market == "tether":
                market = "usdt"
            try:
                coin = models.Coin.objects.get(title__iexact=title)
            except models.Coin.DoesNotExist:
                errors += f"\n\nerror: Coin {title} not found\nrow: {row}"
                fail_counter += 1
                continue
            platform_id_components = [
                str(date).split()[0],
                coin.code,
                market,
                trade_type,
                str(float(amount)),
                str(float(price)),
            ]
            platform_id = "|".join(platform_id_components).lower()
            try:
                transaction_data = {
                    "coin": coin,
                    "type": trade_type,
                    "quantity": Decimal(amount),
                    "price": Decimal(price),
                    "jdate": date,
                    "profile": importer.profile,
                    "market": market,
                }
                _, created = models.Transaction.objects.update_or_create(
                    platform_id=platform_id, defaults=transaction_data
                )
                if created:
                    success_counter += 1
            except Exception as e:
                errors += f"\n\nerror:{e}\nrow: {row}"
                fail_counter += 1

    models.Importer.objects.filter(pk=importer_id).update(
        errors=errors, success_count=success_counter, fail_count=fail_counter
    )


@shared_task
def update_transaction_ids():
    transactions = models.Transaction.objects.select_related("coin")
    updated_transactions = []

    for transaction in transactions:
        platform_id_components = [
            str(transaction.jdate).split()[0],
            transaction.coin.code,
            transaction.market,
            transaction.type,
            str(float(transaction.quantity)),
            str(float(transaction.price)),
        ]
        transaction.platform_id = "|".join(platform_id_components).lower()
        updated_transactions.append(transaction)

    models.Transaction.objects.bulk_update(updated_transactions, ["platform_id"])
