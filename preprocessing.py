# these should be in project.py
# but keep this here for easier testing
import psycopg2
from annotation import Annotator
# username = "postgres"
# password = "admin"
# host = "localhost"
# database = "cz4031" # "TPC-H"
#
# conn = psycopg2.connect(
#     dbname=database,
#     user=username,
#     host=host,
#     password=password
# )
#
# cur = conn.cursor()
# query = "explain (format json) insert into region values (5, 'Singapore', 'little comment')"
# # query = "EXPLAIN (FORMAT JSON) INSERT INTO region VALUES (5, 'SINGAPORE', 'little comment')"
# cur.execute(query)
# rows = cur.fetchall()
# for row in rows:
#     print (row)


# actual preprocessing stuff:
class QueryProcessor:

    def __init__(self, username, password, host, database):
        # self.username = username
        # self.password = password
        # self.host = host
        # self.database = database
        conn = psycopg2.connect(
            dbname=database,
            user=username,
            host=host,
            password=password
        )

        self.cur = conn.cursor()
        self.annotator = Annotator()

    def process_query(self, query):
        self.cur.execute("EXPLAIN (FORMAT JSON) " + query)
        query_plan = self.cur.fetchall()[0][0][0]["Plan"]  # extract only the plan

        self.annotator.annotate(query_plan)

qp = QueryProcessor("postgres", "admin", "localhost", "cz4031")
# qp.process_query("SELECT * FROM customer, nation, supplier WHERE nation.n_nationkey = 0")
# qp.process_query("INSERT INTO region VALUES (5, 'SINGAPORE', 'little comment')")
# qp.process_query("select * from customer c, orders o where c.c_custkey = o.o_custkey")
qp.process_query("select * from customer c where c.c_custkey = ( select o_orderkey from orders where o_custkey = 4 )")