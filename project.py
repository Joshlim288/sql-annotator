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
        print(e)

# Input variables we need from the interface
username = "postgres"
password = "admin"
host = "localhost"
database = "TPC-H"
# q1 = "SELECT * FROM customer, nation , supplier WHERE nation.n_nationkey = 0"
# q1 = "INSERT INTO region VALUES (5, 'SINGAPORE', 'little comment')"
q1 = "select * from customer c, orders o where c.c_custkey = o.o_custkey"
# q1 = "select * from customer c where c.c_custkey = ( select o_orderkey from orders where o_custkey = 4 )"

processor = QueryProcessor(username, password, host, database)
annotator = Annotator()
print(get_annotated_query(q1))








