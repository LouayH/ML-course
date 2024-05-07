from django.db import models

from accounts.models import User
from pages.models import Meal


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.user.username} ordered {self.quantity} from {self.meal.name}'
