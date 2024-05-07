from pages.models import Meal
from accounts.models import User
from cart.models import Order

import io
import random
import requests


MAIN_INGREDIENTS = sorted([
    'egg', 'chicken', 'rice', 'tomato', 'cheese', 'potato', 'onion', 'garlic', 'butter', 'corn',
    'lemon', 'cucumber', 'fish', 'pasta', 'spinach', 'ginger', 'parsley', 'carrot', 'cinnamon', 'olives',
    'eggplant', 'mushroom', 'bread', 'beef', 'chocolate', 'apple', 'banana', 'orange', 'broccoli', 'peas'
])

def get_main_ingredients(ingredients: str):
    main_ingredients = []
    for ingredient in MAIN_INGREDIENTS:
        if ingredient in ingredients:
            main_ingredients.append(ingredient)
    return main_ingredients


def ingredients_classify(images):
    data = []

    for img in images:
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        data.append(('images', img_byte_arr))

    print(f'number of images: {len(data)}')

    response = requests.post('http://127.0.0.1:5000/ingredients-classifier', files=data)
    return set(response.json()['ingredients'])


def get_meal_recommendation(img):
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    data = {
        'meal_image': img_byte_arr
    }
    response = requests.post('http://127.0.0.1:5000/meal-classifier', files=data)
    payload = response.json()
    ingredients = payload['ingredients']
    recognized_meal = payload['recognized_meal']
    print(f'ingredients: {ingredients}')
    print(f'recognized_meal: {recognized_meal}')
    meals = Meal.objects.values_list('ingredients', 'pk')
    scores = [
        (sum([ingredient in meal for ingredient in ingredients]), pk)
        for meal, pk in meals
    ]
    top3 = [item[1] for item in sorted(scores, reverse=True)[:3]]
    return Meal.objects.filter(pk__in=top3), recognized_meal


def __get_user_features(user):
    # get user orders
    orders = user.orders.values_list('quantity', 'meal__ingredients')

    print('='*20)
    print(f'orders: {orders}')
    print('='*20)

    features = [0] * len(MAIN_INGREDIENTS)
    for order in orders:
        for i, ingredient in enumerate(MAIN_INGREDIENTS):
            if ingredient in order[1]:
                features[i] += order[0]

    age = user.age
    gender = user.gender == 'male'

    features.extend([age, gender])

    return features


def get_personal_recommendation(user):
    # get features
    features = __get_user_features(user)

    data = {'features': features}
    response = requests.post('http://127.0.0.1:5000/personal-recommender', json=data)
    # inference
    # scores = personal_recommender.predict([features])[0].tolist()
    # scores = zip(scores, range(len(scores)))
    payload = response.json()
    top30 = payload["top30"]
    # shuffle to ensure that recommendations are not only what the user bought earlier
    random.shuffle(top30)
    recommendations = top30[:3]
    return Meal.objects.filter(pk__in=recommendations)



class Plot:
    def __init__(self, title, data):
        self.title = title
        self.data = data


def __extract_ingredients(orders):
    ingredients = []
    for order in orders:
        for i, ingredient in enumerate(MAIN_INGREDIENTS):
            if ingredient in order:
                ingredients.append(ingredient)

    return ingredients


def get_orders():
    def flatten_orders(orders):
      flattened_orders = []
      for order in orders:
          flattened_orders.extend([order[1:]]*order[0])
      return flattened_orders

    orders = Order.objects.select_related('user', 'meal').values_list('quantity', 'meal__ingredients', 'user__age', 'user__gender')
    orders = list(orders)

    # repeat by quantity, and keep only ingredients and meal id
    orders = flatten_orders(orders)

    orders_ingredients = __extract_ingredients([order[0] for order in orders])
    orders = [(ingredients, *order[1:]) for ingredients, order in zip(orders_ingredients, orders)]

    return orders


def get_plots():

    def get_plot(payload, plot_name, plot_title):
        return Plot(plot_title, payload[plot_name])
    
    plots = []

    # data
    age_data = User.objects.values_list('age', flat=True)
    age_data = list(age_data)

    gender_data = User.objects.values_list('gender', flat=True)
    gender_data = list(gender_data)

    ingredients_data = Meal.objects.values_list('ingredients', flat=True)
    ingredients_data = __extract_ingredients(ingredients_data)

    orders_data = get_orders()

    data = {
        "age": age_data,
        "gender": gender_data,
        "ingredients": ingredients_data,
        "orders": orders_data
    }
    response = requests.post(f'http://127.0.0.1:5000/data-analysis', json=data)
    print(f'response: {response}')
    payload = response.json()
    print(f'payload: {payload}')

    plots.append(get_plot(payload, 'age-hist', "توزع الأعمار"))
    plots.append(get_plot(payload, 'age-pie', "نسب الأعمار"))
    plots.append(get_plot(payload, 'gender-bar', "توزع الجنس"))
    plots.append(get_plot(payload, 'gender-pie', "نسب الجنس"))
    plots.append(get_plot(payload, 'gender-age-scatter', "توزع العمر بالنسبة للجنس"))
    plots.append(get_plot(payload, 'ingredients-hist', "توزع المكونات"))
    plots.append(get_plot(payload, 'ingredients-orders-hist', "توزع المكونات المباعة"))
    plots.append(get_plot(payload, 'ingredients-age-scatter', "توزع الأعمار بالنسبة للمكونات"))
    plots.append(get_plot(payload, 'ingredients-gender-scatter', "توزع الجنس بالنسبة للمكونات"))
    plots.append(get_plot(payload, 'ingredients-male-hist', "توزع المكونات للذكور"))
    plots.append(get_plot(payload, 'ingredients-female-hist', "توزع المكونات للإناث"))

    return plots

