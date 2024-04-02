import mysql.connector
import pandas as pd
from datetime import datetime

def connect():
  connection = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "",
    database = "wp-ecommerce"
  )

  cursor = connection.cursor(dictionary = True)

  return connection, cursor

# 04-find-associations-rules

def get_product_title(cursor, product_id):
  sql = '''
    SELECT post_title FROM wp_posts WHERE ID = (%s)
  '''
  
  cursor.execute(sql, (product_id, ))
  
  result = cursor.fetchone()

  return result["post_title"] if result else None

def build_transactions(cursor):
  sql = '''
    SELECT * FROM wp_wc_order_stats ORDER BY order_id
  '''
  
  cursor.execute(sql)

  results = cursor.fetchall()

  data = pd.DataFrame(columns = [0, 1, 2, 3, 4])
  
  for row in results:
    order_id = row["order_id"]

    sql = '''
      SELECT * FROM wp_wc_order_product_lookup WHERE order_id = (%s)
    '''
  
    cursor.execute(sql, (order_id, ))
    
    order_products = cursor.fetchall()

    product_ids = []

    for product in order_products:
      product_id = product["product_id"]

      if product_id > 0:
        product_ids.append(product_id)

    if len(product_ids) > 1:
      data = pd.concat([data, pd.DataFrame([product_ids])], ignore_index = True)
  
  return data

def export_associations_rules(connection, cursor, rules):
  sql = "DROP TABLE IF EXISTS wp_wc_product_associations"
  
  cursor.execute(sql)

  sql = '''
    CREATE TABLE wp_wc_product_associations (
      ID int(11) NOT NULL AUTO_INCREMENT,
      antecedent_product_id int(11) NOT NULL,
      antecedent_product_title text NOT NULL,
      consequent_product_id int(11) NOT NULL,
      consequent_product_title text NOT NULL,
      confidence double NOT NULL,
      PRIMARY KEY (ID)
    )
  '''
  
  cursor.execute(sql)
  
  connection.commit()

  for rule in rules.itertuples():
    antecedents = rule.antecedents
    consequents = rule.consequents
    confidence = rule.confidence * 100

    for antecedent_product_id in antecedents:
      antecedent_product_title = get_product_title(cursor, antecedent_product_id)

      for consequent_product_id in consequents:
        consequent_product_title = get_product_title(cursor, consequent_product_id)
        
        # delete association rule with low confidence
        sql = '''
          DELETE FROM wp_wc_product_associations
          WHERE antecedent_product_id = (%s)
          AND consequent_product_id = (%s)
          AND confidence < (%s)
        '''
  
        cursor.execute(sql, (antecedent_product_id, consequent_product_id, confidence))

        # get association rule with accepted or better confidence
        sql = '''
          SELECT * FROM wp_wc_product_associations
          WHERE antecedent_product_id = (%s)
          AND consequent_product_id = (%s)
          AND confidence >= (%s)
        '''
  
        cursor.execute(sql, (antecedent_product_id, consequent_product_id, confidence))

        result = cursor.fetchone()

        # insert association rule if not stored in the table
        insert_association = False if result else True

        if insert_association:
          sql = '''
            INSERT INTO wp_wc_product_associations VALUES (NULL, %s, %s, %s, %s, %s)
          '''
  
          cursor.execute(sql, (antecedent_product_id, antecedent_product_title,
                              consequent_product_id, consequent_product_title,
                              confidence))
    
          connection.commit()

def get_recommended_products_by_product(product_id):
  _, cursor = connect()

  sql = '''
    SELECT * FROM wp_wc_product_associations
    WHERE antecedent_product_id = (%s)
    ORDER BY confidence DESC
  '''
  
  cursor.execute(sql, (product_id, ))

  results = cursor.fetchall()

  entries = []

  for row in results:
    entries.append({
      "product_id": row["consequent_product_id"],
      "product_title": row["consequent_product_title"],
      "confidence": round(row["confidence"], 2)
    })
  
  data = pd.DataFrame(entries)

  return data

# 05-products-by-customer-classification.ipynb

def get_category_title(category_id):
  _, cursor = connect()

  sql = '''
    SELECT name FROM wp_terms
    LEFT JOIN wp_term_taxonomy ON wp_terms.term_id = wp_term_taxonomy.term_id
    WHERE wp_term_taxonomy.taxonomy = 'product_cat'
    AND wp_terms.term_id = (%s)
  '''

  cursor.execute(sql, (category_id, ))

  result = cursor.fetchone()

  return result["name"] if result else None

def get_product_categories(product_id):
  _, cursor = connect()

  sql = '''
    SELECT wp_term_relationships.object_id, wp_term_taxonomy.term_id
    FROM wp_term_relationships
    INNER JOIN wp_term_taxonomy ON wp_term_taxonomy.term_taxonomy_id = wp_term_relationships.term_taxonomy_id
    WHERE wp_term_taxonomy.taxonomy = 'product_cat'
    AND wp_term_relationships.object_id = (%s)
  '''

  cursor.execute(sql, (product_id, ))

  results = cursor.fetchall()

  category_ids = []

  for row in results:
    category_ids.append(row["term_id"])

  return category_ids

def add_to_category_list(category_list, term_id, customer_id):
  for category in category_list:
    if category["term_id"] == term_id and category["customer_id"] == customer_id:
      category["count"] += 1
      return None
    
  category =  {
    "term_id": term_id,
    "customer_id": customer_id,
    "count": 1
  }

  category_list.append(category)

def build_category_by_customer_data():
  _, cursor = connect()

  sql = "SELECT ID FROM wp_users ORDER BY ID"

  cursor.execute(sql)

  results = cursor.fetchall()

  entries = []
  for row in results:
    user_id = row["ID"]

    # check if user is customer
    sql = '''
      SELECT * FROM wp_wc_customer_lookup WHERE user_id = (%s)
    '''

    cursor.execute(sql, (user_id, ))
    result = cursor.fetchone()
    customer_id = result["customer_id"] if result else None

    if customer_id:
      # get user's meta
      sql = '''
        SELECT * FROM wp_usermeta WHERE user_id = (%s) and meta_key IN ('country', 'age', 'gender')
      '''

      cursor.execute(sql, (user_id, ))
      usermeta = cursor.fetchall()

      country_meta = next(meta for meta in usermeta if meta["meta_key"] == "country")
      country = country_meta["meta_value"] if country_meta else "unknown"

      age_meta = next(meta for meta in usermeta if meta["meta_key"] == "age")
      age = age_meta["meta_value"] if age_meta else "unknown"

      gender_meta = next(meta for meta in usermeta if meta["meta_key"] == "gender")
      gender = gender_meta["meta_value"] if gender_meta else "unknown"

      # get purchased products by the customer
      sql = '''
        SELECT * from wp_wc_order_product_lookup WHERE customer_id = (%s)
      '''
      
      cursor.execute(sql, (customer_id, ))

      order_products = cursor.fetchall()

      category_list = []
      for product in order_products:
        customer_id = product["customer_id"]
        product_id = product["product_id"]

        term_ids = get_product_categories(product_id)

        for term_id in term_ids:
          add_to_category_list(category_list, term_id, customer_id)

      category_list = sorted(category_list, key = lambda c: c["count"], reverse = True)

      if len(category_list) > 0:
        term_id = category_list[0]["term_id"]
        term_title = get_category_title(term_id)
        purchase_count = category_list[0]["count"]

        entries.append({
          "user_id": user_id,
          "customer_id": customer_id,
          "country": country,
          "age": age,
          "gender": gender,
          "term_id": term_id,
          "term_title": term_title,
          "purchase_count": purchase_count,
        })
  
  data = pd.DataFrame(entries)

  return data

def export_country_codes(encoder):
  connection, cursor = connect()

  sql = "DROP TABLE IF EXISTS wp_wc_country_codes"
  
  cursor.execute(sql)

  sql = '''
    CREATE TABLE wp_wc_country_codes (
      ID int(11) NOT NULL AUTO_INCREMENT,
      country char(2) NOT NULL,
      code int(11) NOT NULL,
      PRIMARY KEY (ID)
    )
  '''
  
  cursor.execute(sql)
  
  connection.commit()

  for country in encoder.classes_:
    code = encoder.transform([country])[0]
    code = int(code)

    sql = '''
      INSERT INTO wp_wc_country_codes VALUES (NULL, %s, %s)
    '''

    cursor.execute(sql, (country, code))
  
    connection.commit()

def get_country_code(country):
  _, cursor = connect()

  sql = '''
    SELECT code FROM wp_wc_country_codes WHERE country = (%s)
  '''
  
  cursor.execute(sql, (country, ))
  
  result = cursor.fetchone()

  return result["code"] if result else None

def export_gender_codes(encoder):
  connection, cursor = connect()

  sql = "DROP TABLE IF EXISTS wp_wc_gender_codes"
  
  cursor.execute(sql)

  sql = '''
    CREATE TABLE wp_wc_gender_codes (
      ID int(11) NOT NULL AUTO_INCREMENT,
      gender char(10) NOT NULL,
      code int(11) NOT NULL,
      PRIMARY KEY (ID)
    )
  '''
  
  cursor.execute(sql)
  
  connection.commit()

  for gender in encoder.classes_:
    code = encoder.transform([gender])[0]
    code = int(code)

    sql = '''
      INSERT INTO wp_wc_gender_codes VALUES (NULL, %s, %s)
    '''

    cursor.execute(sql, (gender, code))
  
    connection.commit()

def get_gender_code(gender):
  _, cursor = connect()

  sql = '''
    SELECT code FROM wp_wc_gender_codes WHERE gender = (%s)
  '''
  
  cursor.execute(sql, (gender, ))
  
  result = cursor.fetchone()

  return result["code"] if result else None

def get_best_seller_products_by_category(category_id, limit):
  _, cursor = connect()

  sql = '''
    SELECT wp_term_taxonomy.term_id, wp_wc_order_product_lookup.product_id, sum(wp_wc_order_product_lookup.product_qty) sales
    FROM wp_wc_order_product_lookup
    INNER JOIN wp_term_relationships ON wp_term_relationships.object_id = wp_wc_order_product_lookup.product_id
    INNER JOIN wp_term_taxonomy ON wp_term_taxonomy.term_taxonomy_id = wp_term_relationships.term_taxonomy_id
    WHERE wp_term_taxonomy.taxonomy = 'product_cat'
    AND wp_term_taxonomy.term_id = (%s)
    GROUP BY wp_term_taxonomy.term_id, wp_wc_order_product_lookup.product_id
    ORDER BY sales DESC
    LIMIT %s
  '''

  cursor.execute(sql, (category_id, limit))

  results = cursor.fetchall()

  product_ids = [row["product_id"] for row in results]

  return product_ids

def predict_category_by_customer(model, customer_details):
  prediction = model.predict([customer_details])

  return prediction[0]

def get_recommended_products_by_customer(model, customer_id, limit):
  _, cursor = connect()

  sql = '''
    SELECT user_id FROM wp_wc_customer_lookup WHERE customer_id = (%s)
  '''
  
  cursor.execute(sql, (customer_id, ))
  
  result = cursor.fetchone()

  user_id = result["user_id"] if result else None

  # get user's meta
  sql = '''
    SELECT * FROM wp_usermeta WHERE user_id = (%s) and meta_key IN ('country', 'age', 'gender')
  '''

  cursor.execute(sql, (user_id, ))
  usermeta = cursor.fetchall()

  country_meta = next(meta for meta in usermeta if meta["meta_key"] == "country")
  country = country_meta["meta_value"] if country_meta else "unknown"
  country = get_country_code(country)

  age_meta = next(meta for meta in usermeta if meta["meta_key"] == "age")
  age = age_meta["meta_value"] if age_meta else "unknown"

  gender_meta = next(meta for meta in usermeta if meta["meta_key"] == "gender")
  gender = gender_meta["meta_value"] if gender_meta else "unknown"
  gender = get_gender_code(gender)

  predicted_category_id = predict_category_by_customer(model, [country, age, gender])

  recommended_product_ids = get_best_seller_products_by_category(int(predicted_category_id), limit)

  return recommended_product_ids

# 07-predict-future-sales

def get_last_sale_date():
  _, cursor = connect()

  sql = '''
    SELECT Left(MAX(date_created), 10) date
    FROM wp_wc_order_product_lookup
  '''

  cursor.execute(sql)

  result = cursor.fetchone()

  last_sale_date = datetime.strptime(result["date"], "%Y-%m-%d")

  return last_sale_date

def get_sales_between_two_dates(start_date, end_date):
  _, cursor = connect()

  sql = '''
    SELECT LEFT(date_created, 10) as date, sum(product_net_revenue) as sales
    FROM wp_wc_order_product_lookup
    WHERE date_created BETWEEN (%s) AND (%s)
    GROUP BY date
    ORDER BY date
  '''

  cursor.execute(sql, (start_date, end_date))

  results = cursor.fetchall()

  entries = []
  for row in results:
    entries.append({
      "date": row["date"],
      "sales": row["sales"]
    })
  
  data = pd.DataFrame(entries)

  return data

def export_sales_forecast(forecast):
  connection, cursor = connect()

  sql = "DROP TABLE IF EXISTS wp_wc_sales_forecast"
  
  cursor.execute(sql)

  sql = '''
    CREATE TABLE wp_wc_sales_forecast (
      ID int(11) NOT NULL AUTO_INCREMENT,
      date datetime NOT NULL,
      sales float NOT NULL,
      PRIMARY KEY (ID)
    )
  '''
  
  cursor.execute(sql)
  
  connection.commit()

  for index, row in forecast.iterrows():
    date = index.strftime("%Y-%m-%d")
    sales = float(row[0])

    sql = '''
      INSERT INTO wp_wc_sales_forecast VALUES (NULL, %s, %s)
    '''
  
    cursor.execute(sql, (date, sales))
    
    connection.commit()

def get_sales_forecast():
  _, cursor = connect()

  sql = "SELECT * FROM wp_wc_sales_forecast"
  
  cursor.execute(sql)

  results = cursor.fetchall()

  entries = []
  for row in results:
    entries.append({
      "date": row["date"],
      "sales": row["sales"],
    })
  
  data = pd.DataFrame(entries)

  return data