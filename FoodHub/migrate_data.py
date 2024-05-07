import sqlite3
import string
import shutil
import os
import pandas as pd


DATASET_PATH = 'Absolute path to the dataset folder'

IMAGES_PATH = DATASET_PATH + '/Food Images/Food Images'

CSV_PATH = DATASET_PATH + '/Food Ingredients and Recipe Dataset with Image Name Mapping.csv'

DATABASE_PATH = './food_app/db.sqlite3'

# preprocess dataset
df = pd.read_csv(CSV_PATH, index_col=0)


titles = df['Title']
titles.dropna(inplace=True)

chars = set()

for title in titles:
    for char in title:
        chars.add(char)

chars = sorted(chars)

expected_chars = string.ascii_letters + string.digits + ' ' + '"&\'()-'
unexpected_chars = [char for char in chars if char not in expected_chars]

# Remove empty values
df = df.dropna()

# remove duplicates
df = df.drop_duplicates(subset=['Title'])

for char in unexpected_chars:
    df = df[df['Title'].str.contains(char, regex=False) == False]


connection = sqlite3.connect(DATABASE_PATH)

cur = connection.cursor()
data = []
cnt = 100
for index, row in df.iterrows():
    if cnt == 0:
        break
    cnt -= 1
    row['Image_Name'] = row['Image_Name'] + '.jpg'
    img_name = row['Image_Name']
    src = IMAGES_PATH + os.path.sep + img_name
    dst = './food_app/media/meals' + os.path.sep + img_name
    shutil.copyfile(src, dst)
    row['Image_Name'] = 'meals/' + row['Image_Name']
    item = [row[col] for col in df.columns][:-1] + [0]

    data.append(tuple(item))
cur.executemany(
    "INSERT INTO pages_meal (name, ingredients, instructions, img, price) VALUES (?, ?, ?, ?, ?)",
    data
)
connection.commit()
connection.close()
