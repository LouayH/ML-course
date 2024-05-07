from django.db import models


class Meal(models.Model):
    name = models.CharField(null=False, blank=False, max_length=100)
    img = models.ImageField(upload_to='meals/')
    ingredients = models.TextField(max_length=2500)
    instructions = models.TextField(max_length=13000)
    price = models.FloatField(default=0)

    def __str__(self):
        return self.name
