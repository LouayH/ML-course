from django.urls import path

from .views import IngredientsClassifierView, MealsClassifierView


urlpatterns = [
    path("ingredients-recognition/", IngredientsClassifierView.as_view(), name="ingredients-recognition"),
    path("meals-recognition/", MealsClassifierView.as_view(), name="meals-recognition"),
]
