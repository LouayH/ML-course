from db import *
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import RandomOverSampler
from sklearn.tree import DecisionTreeClassifier
import pickle

def task():
  data = build_category_by_customer_data()

  # encode categorical features
  countryEncoder = LabelEncoder()
  genderEncoder = LabelEncoder()

  data["country"] = countryEncoder.fit_transform(data["country"])
  data["gender"] = genderEncoder.fit_transform(data["gender"])

  export_country_codes(countryEncoder)
  export_gender_codes(genderEncoder)

  x = data[["country", "age", "gender"]]
  y = data["term_id"]

  # resample imbalanced classes
  resample = RandomOverSampler()
  x, y = resample.fit_resample(x, y)

  # create the model
  model = DecisionTreeClassifier()
  model.fit(x.values, y.values)

  # save the model
  filename = "classification-model"
  pickle.dump(model, open(filename, "wb"))