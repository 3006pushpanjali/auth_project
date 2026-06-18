import uuid

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    is_email_verified = models.BooleanField(
        default=False
    )

    email_verification_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    password_reset_token = models.UUIDField(
        null=True,
        blank=True,
        unique=True
    )
    
    def __str__(self):
        return self.user.username