import psycopg2
username = "postgres"
password = "admin"
host = "localhost"
database = "TPC-H"

conn = psycopg2.connect(
    dbname=database,
    user=username,
    host=host,
    password=password
)

cur = conn.cursor()
query = "SELECT * FROM nation"
cur.execute(query)
rows = cur.fetchall()
for row in rows:
    print (row)
#cur.execute(cur.mogrify('explain analyze ' + query, vals))
#analyze_fetched = cur.fetchall()
#print(analyze_fetched)