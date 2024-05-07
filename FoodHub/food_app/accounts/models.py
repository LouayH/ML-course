from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    age = models.PositiveSmallIntegerField()
    gender_choices = [('male', 'ذكر'), ('female', 'أنثى')]
    gender = models.CharField(max_length=6, null=False, blank=False, choices=gender_choices)

    REQUIRED_FIELDS = ['age', 'gender']
