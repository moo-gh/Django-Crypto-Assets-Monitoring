from django.db import models
from django.contrib.auth.models import AbstractUser

from reusable.models import BaseModel


class Profile(AbstractUser):
    mobile_number = models.SlugField(max_length=11, null=True, blank=True, unique=True)
    combine_notifications = models.BooleanField(
        default=False, help_text="Combine multiple notifications into a single message"
    )

    def __str__(self):
        return f"({self.pk} - {self.mobile_number})"

    @property
    def telegram_account(self):
        return self.telegram_accounts.last()


class Channel(BaseModel):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="channels"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    channel_identifier = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"({self.pk} - {self.name})"


class TelegramAccount(BaseModel):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="telegram_accounts"
    )
    chat_id = models.IntegerField(unique=True)

    def __str__(self):
        return f"({self.profile.mobile_number} - {self.chat_id})"
