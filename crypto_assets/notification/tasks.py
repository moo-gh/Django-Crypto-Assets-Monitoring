from datetime import datetime

from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Q

from crypto_assets.celery import app
from . import models, utils

logger = get_task_logger(__name__)


def reset_notifications_last_sent():
    affected_count = models.Notification.objects.filter(~Q(status=None)).update(
        last_sent=None
    )
    print(f"Reset last_sent for {affected_count} notifications")


@app.task(name="check_coin_notifications")
def check_coin_notifications():
    # This task will check all notifications and send a telegram message,
    #  if the price is reached
    # User can set a notification for a coin's price and market
    #  and if the target hit, a telegram message will be sent
    # User should define when the notification should be sent, at
    #   upper or lower price
    bot_token = settings.TELEGRAM_BOT_TOKEN
    prices = utils.get_coin_cached_prices()
    if not prices:
        return

    starting_task_time = datetime.now()

    # check notifications randomly
    notifications = models.Notification.objects.filter(~Q(status=None)).order_by("pk")

    # Dictionary to store combined notifications by profile
    combined_messages = {}

    notifications_should_be_updated = []

    for notification in notifications:
        tg_account = notification.profile.telegram_account.chat_id
        if not tg_account:
            continue

        coin_key = f"{notification.coin.code}_{notification.market}".lower()
        price = prices.get(coin_key)
        if price is None:
            continue

        price_repr = f"{float(price):,}"
        message = f"{notification.coin.code}: {price_repr} {notification.market}"

        send_message = False

        if (
            price > notification.price
            and notification.status == models.Notification.UPPER
        ):
            message = f"🟢 {message}"
            if notification.interval:
                if not notification.passed_interval:
                    continue
            else:
                notification.status = None
            send_message = True
        if (
            price < notification.price
            and notification.status == models.Notification.LOWER
        ):
            message = f"🔴 {message}"
            if notification.interval:
                if not notification.passed_interval:
                    continue
            else:
                notification.status = None
            send_message = True

        if not send_message:
            continue

        # If user wants to combine notifications, add to dictionary
        if notification.profile.combine_notifications:
            # send to channel or directly to user
            if notification.channel:
                channel_id = notification.channel.channel_identifier
                if channel_id not in combined_messages:
                    combined_messages[channel_id] = []
                combined_messages[channel_id].append(message)
            else:
                if tg_account not in combined_messages:
                    combined_messages[tg_account] = []
                combined_messages[tg_account].append(message)
            notifications_should_be_updated.append(notification.pk)
        else:
            # Send separate message to channel if available
            if notification.channel:
                utils.send_telegram_message(
                    settings.TELEGRAM_BOT_TOKEN,
                    notification.channel.channel_identifier,
                    message,
                )
            else:
                # Send message to user's telegram account immediately
                if tg_account:
                    utils.send_telegram_message(bot_token, tg_account, message)

            notification.last_sent = starting_task_time
            notification.save()

    # Send combined messages
    for chat_id, messages in combined_messages.items():
        if not messages:
            continue
        combined_text = "\n".join(messages)
        utils.send_telegram_message(bot_token, chat_id, combined_text)
    # bulk update notifications' last_sent to starting_task_time
    models.Notification.objects.filter(id__in=notifications_should_be_updated).update(
        last_sent=starting_task_time
    )


def format_message(transaction, change_percentage):
    """
    Format the message to be sent to the user
    """
    icon = "🟢" if change_percentage >= 0 else "🔴"
    message = f"{icon} #{transaction.pk}"
    message += f"\n\ncoin: {transaction.coin.code} {transaction.market.upper()}"
    message += f"\nquantity: {transaction.quantity}"
    message += f"\nbought price: {transaction.get_price}"
    message += f"\ncurrent price: {transaction.get_current_price}"
    message += f"\n\nprofit/loss percentage: {change_percentage}%"
    message += f"\nprofit/loss value: {transaction.get_profit_or_loss}"
    return message


@app.task(name="check_transaction_notifications")
def check_transaction_notifications():
    """
    Check all notifications and send a telegram message if the percentage is reached
    """
    notifications = (
        models.Notification.objects.filter(
            transaction__isnull=False, percentage__isnull=False
        )
        .select_related("transaction", "profile", "channel")
        .order_by("?")
    )

    # Dictionary to store combined notifications by profile
    combined_messages = {}

    for notification in notifications:
        transaction = notification.transaction
        change_percentage = transaction.get_change_percentage
        should_notify = (
            notification.status == models.Notification.UPPER
            and change_percentage >= notification.percentage
        ) or (
            notification.status == models.Notification.LOWER
            and change_percentage <= notification.percentage
        )

        if should_notify:
            message = format_message(transaction, change_percentage)

            # If user wants to combine notifications, add to dictionary
            if notification.profile.combine_notifications:
                tg_account = notification.profile.telegram_account.chat_id
                if tg_account not in combined_messages:
                    combined_messages[tg_account] = []
                combined_messages[tg_account].append(message)

                # Add channel messages to a separate entry if channel exists
                if notification.channel:
                    channel_id = notification.channel.channel_identifier
                    if channel_id not in combined_messages:
                        combined_messages[channel_id] = []
                    combined_messages[channel_id].append(message)
            else:
                # Send message to user's telegram account immediately
                utils.send_telegram_message(
                    settings.TELEGRAM_BOT_TOKEN,
                    notification.profile.telegram_account.chat_id,
                    message,
                )

                # Send message to channel if available
                if notification.channel:
                    # Use channel's identifier directly as chat_id
                    utils.send_telegram_message(
                        settings.TELEGRAM_BOT_TOKEN,
                        notification.channel.channel_identifier,
                        message,
                    )

    # Send combined messages
    for chat_id, messages in combined_messages.items():
        if messages:
            combined_text = "📊 Favorite Crypto Transactions \n\n" + "\n\n".join(
                messages
            )
            utils.send_telegram_message(
                settings.TELEGRAM_BOT_TOKEN, chat_id, combined_text
            )
