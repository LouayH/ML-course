from django.urls import path

from .views import MealListView, MealDetailView, HomePageView, SearchView, DataAnalysisView


urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('data-analysis/', DataAnalysisView.as_view(), name='data-analysis'),
    path('meals-list/', MealListView.as_view(), name='meals-list'),
    path('meal/<int:pk>/', MealDetailView.as_view(), name='meal-details'),
    path('search/', SearchView.as_view(), name='search'),
]
