import sqlparse

query = "SELECT c.customer_id, c.name FROM customers c;"
parsed = sqlparse.parse(query)
stmt = parsed[0]
# Visualize the tree structure
stmt._pprint_tree()