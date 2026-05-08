from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Plan(models.TextChoices):
        FREE = "free", "無料プラン"
        PAID = "paid", "有償プラン"

    username = None
    email = models.EmailField(unique=True)

    plan = models.CharField(max_length=10, choices=Plan.choices, default=Plan.FREE)
    plan_started_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def is_paid(self):
        return self.plan == self.Plan.PAID
