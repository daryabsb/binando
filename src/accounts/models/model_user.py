from django.db import models
from src.accounts.managers import UserManager
# from src.configurations.models import SecurityKey
from src.core.modules import upload_image_file_path
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin


class User(PermissionsMixin, AbstractBaseUser):
    # Custom user model supports email instead of username
    # access_level = models.OneToOneField(
    #     "SecurityKey", on_delete=models.CASCADE, null=True,
    #     blank=True, related_name="access_level"
    # )
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(
        null=True, blank=True, default='user.png',
        upload_to=upload_image_file_path)
    pin = models.SmallIntegerField(default=1699)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
