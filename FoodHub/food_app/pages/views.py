from django.views.generic import ListView, DetailView, TemplateView
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin



from .models import Meal
from ai_components.helpers import get_main_ingredients, get_personal_recommendation
from ai_components.helpers import get_plots


class HomePageView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context['recommended_meals'] = get_personal_recommendation(self.request.user)
        
        return context


class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class DataAnalysisView(SuperuserRequiredMixin, TemplateView):
    template_name = "pages/data-analysis.html"

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)

        try:
            context['plots'] = get_plots()
            msg = "تم تحميل المخططات بنجاح"
        except:
            msg = "خطأ في تحميل المخططات، أعد المحاولة مجدداُ"

        context['msg'] = msg

        return context


class SearchView(View):
    def post(self, request):
        q = request.POST['search']
        url = f'{reverse("meals-list")}?q={q}'
        return HttpResponseRedirect(url)


class MealListView(ListView):
    template_name = 'pages/meals_list.html'
    model = Meal
    context_object_name = 'meals'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        context['ingredients'] = self.request.GET.getlist("ingredients")
        context['recognized_meal'] = self.request.GET.get("recognized_meal")

        return context

    def get_queryset(self):
        query = super().get_queryset()

        if 'recommended_meals' in self.request.GET:
            recommended_meals = self.request.GET.getlist("recommended_meals")
            print(f'recommended meals: {recommended_meals}')
            query = query.filter(name__in=recommended_meals)

        if 'q' in self.request.GET:
            q = self.request.GET['q']
            query = query.filter(name__icontains=q)

        if 'ingredients' in self.request.GET:
            print(f'ingredients in meals list: {self.request.GET.getlist("ingredients")}')
            meals = query.values_list('id', 'ingredients')

            meals = [
                (id, set(get_main_ingredients(ingredients)))
                for (id, ingredients) in meals
            ]
            user_ingredients = set(self.request.GET.getlist('ingredients'))
            print(meals[0][1])
            print(user_ingredients)
            meals_scores = [
                (len(user_ingredients.intersection(meal[1])), meal[0]) for meal in meals
            ]
            print(f'meals scores: {sorted(meals_scores, reverse=True)[:5]}')
            meals_ids = [meal[1] for meal in sorted(meals_scores, reverse=True) if meal[0] >= 3][:5]
            query = query.filter(pk__in=meals_ids)
        return query


class MealDetailView(LoginRequiredMixin, DetailView):
    template_name = 'pages/meal.html'
    model = Meal
