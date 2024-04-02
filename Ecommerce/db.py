import mysql.connector
import pandas as pd

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