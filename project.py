from annotation import Annotator
from preprocessing import QueryProcessor

def get_annotated_query(query):
    '''
    Gets annotations for the input query
    :param query: 
    SQL query to be analyzed
    :returns tup: 
    tuple[0] = dictionary where the keys represent a token's index, and the value represents the annotation for that token
    tuple[1]= list of tokens that the query has been split into
    '''
    try:
        query_plan = processor.process_query(query)
        tokenized_query = processor.tokenize_query(query)
        annotation_dict = annotator.annotate(query_plan, tokenized_query)
        return annotation_dict, tokenized_query
    except Exception as e:
        return e

# Input variables we need from the interface
username = "postgres"
password = "admin"
host = "localhost"
database = "cz4031"  # "TPC-H" "cz4031"
# q1 = "SELECT * FROM customer, nation WHERE nation.n_nationkey = 0"
# q1 = "SELECT * FROM customer, nation, supplier WHERE nation.n_nationkey = 0"
# q1 = "INSERT INTO region VALUES (5, 'SINGAPORE', 'little comment')"
# q1 = "update customer set c_name = 'tom' where c_custkey = 1"
# q1 = "delete from region where r_regionkey = 1"
# q1 = "select * from customer c, orders o where c.c_custkey = o.o_custkey"
# q1 = "select * from customer c where c.c_custkey = ( select o_orderkey from orders where o_custkey = 4 )"
# q1 = "select * from customer c, lineitem l1 where c.c_custkey = ( select o_orderkey from orders where o_custkey = 4 and l1.l_partkey = 5 ) and l1.l_suppkey = 7"
# q1 = "select avg(c_acctbal) from customer where c_custkey < 5"
# q1 = "select c_nationkey, c_mktsegment, sum(c_acctbal) from customer where c_custkey < 10 group by c_nationkey, c_mktsegment"
# q1 = "select c_nationkey from customer c where c.c_custkey = ( select o_orderkey from orders where o_custkey = 4 ) group by c_nationkey"
# q1 = "select c_nationkey, c_name from customer c where c.c_custkey = ( select o_orderkey from orders where o_custkey = 4 ) group by c_nationkey, c_name order by c_name"
# q1 = "select c.c_name from customer c where c.c_nationkey IN ( select n.n_nationkey from nation n, region r where r_regionkey < 5 )"  # from with single table that needs join
# q1 = "select * from customer c, orders o where c.c_custkey = 5 or o.o_custkey = 5"

# test double bracket
# q1 = "select * from customer c, lineitem l1 where c.c_custkey = ( select o_orderkey from orders where o_custkey = 4 and l1.l_partkey = 5 ) and l1.l_suppkey = ( select ps_suppkey from partsupp where ps_availqty = 4 )"
# test nested loop is a subplan
q1 = "select * from customer c, lineitem l1 where c.c_custkey = ( select o_orderkey from orders, lineitem l2 where o_custkey = 4 and l2.l_partkey = 5) and l1.l_suppkey = 7"

try:   
    processor = QueryProcessor(username, password, host, database)
except Exception as e:
    print(e)

annotator = Annotator()
try:
    annotated_dict, tokenized_query = get_annotated_query(q1)
    print(annotated_dict)
    print(list(enumerate(tokenized_query)))
except Exception:
    print(get_annotated_query(q1))