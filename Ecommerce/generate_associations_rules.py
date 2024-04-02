from db import *
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules

def encode_transactions(transactions):
  transactions = transactions.T

  transactions = transactions.apply(lambda x: x.dropna().tolist())

  transactions = transactions.tolist()

  encoder = TransactionEncoder()

  encoded_transactions = encoder.fit_transform(transactions)

  data = pd.DataFrame(encoded_transactions, columns = encoder.columns_)

  return data

def generate_association_rules(transactions, min_support, min_confidence):
  frequent_itemsets = apriori(transactions, min_support = min_support, use_colnames = True)
  frequent_itemsets["length"] = frequent_itemsets["itemsets"].apply(lambda x: len(x))

  rules = association_rules(frequent_itemsets, metric = "confidence", min_threshold = min_confidence)
  rules = rules.sort_values("confidence", ascending = False)

  return rules

def task():
  connection, cursor = connect()

  transactions = build_transactions(cursor)

  transactions = encode_transactions(transactions)

  rules = generate_association_rules(transactions, 0.001, 0.01)

  export_associations_rules(connection, cursor, rules)

  connection.close()