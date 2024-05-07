from django.views import View
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.contrib import messages

from pages.models import Meal
from .models import Order


class OrderView(View):
    def post(self, request):
        payload = request.POST
        if 'meal_id' not in payload or 'quantity' not in payload:
            return HttpResponseBadRequest('payload must contain: {"username", "meal_id", and "quantity"}')

        user = request.user
        meal_id = payload['meal_id']
        quantity = payload['quantity']

        print(f'username: {user.username}')
        print(f'meal_id: {meal_id}')
        print(f'quantity: {quantity}')

        meal = get_object_or_404(Meal, pk=meal_id)

        Order.objects.create(user=user, meal=meal, quantity=quantity)

        messages.info(request, f"You have successfully ordered {quantity} from '{meal.name}'")

        next = payload.get('next')
        return HttpResponseRedirect(next)
