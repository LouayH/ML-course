from django.views import generic, View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import IngredientsImagesForm, MealsImagesForm
from .helpers import ingredients_classify, get_meal_recommendation, get_personal_recommendation

from PIL import Image


class IngredientsClassifierView(generic.FormView):
    form_class = IngredientsImagesForm
    template_name = "ai_components/ingredients_recommender.html"  # Replace with your template.

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            # get images from the form
            files = form.cleaned_data["images"]

            images = [Image.open(f.open().file).convert('RGB') for f in files]

            # get the ingredients from the images
            ingredients = ingredients_classify(images)
            print(ingredients)
            # redirect to the meals list page and filter based on the ingredients
            url = reverse('meals-list')
            url = '{}?{}'.format(url, '&'.join([f'ingredients={x}'for x in ingredients]))
            return HttpResponseRedirect(url)
        else:
            return self.form_invalid(form)



class MealsClassifierView(generic.FormView):
    form_class = MealsImagesForm
    template_name = "ai_components/meals_recommender.html"  # Replace with your template.

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        #print(f'form valid? {form.is_valid()}')
        if form.is_valid():
            # get the image from the form
            f= form.cleaned_data["image"]
            image = Image.open(f.open().file).convert('RGB')
            recommended_meals, recognized_meal = get_meal_recommendation(image)
            print(f'recommended_meals: {recommended_meals}')
            # redirect to the meals list page and filter based on the ingredients
            url = reverse('meals-list')
            url = '{}?{}'.format(url, '&'.join(
                [f'recommended_meals={x}'for x in recommended_meals]
                + [f'recognized_meal={recognized_meal}']
            ))
            return HttpResponseRedirect(url)
        else:
            return self.form_invalid(form)
