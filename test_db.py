import psycopg2
username = "postgres"
password = "admin"
host = "localhost"
database = "cz4031" # "TPC-H"

conn = psycopg2.connect(
    dbname=database,
    user=username,
    host=host,
    password=password
)

cur = conn.cursor()
# query = "insert into region values (5, 'Singapore', 'little comment')"
query = "EXPLAIN (FORMAT JSON) INSERT INTO region VALUES (5, 'SINGAPORE', 'little comment')"
cur.execute(query)
rows = cur.fetchall()
for row in rows:
    print (row)
# cur.execute(cur.mogrify('explain analyze ' + query, vals))
# analyze_fetched = cur.fetchall()
# print(analyze_fetched)