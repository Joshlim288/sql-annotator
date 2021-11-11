import psycopg2

# class to handle query pre-processing:
class QueryProcessor:

    def __init__(self, username, password, host, database):
        conn = psycopg2.connect(
            dbname=database,
            user=username,
            host=host,
            password=password
        )
        conn.autocommit = True
        self.cur = conn.cursor()

    def process_query(self, query):
        '''
        Retrieves query plan from Postgresql
        :param query: query to be analyzed
        :returns: query_plan if query is valid
        '''
        num_semicolons = query.count(";")
        if num_semicolons > 1 or (num_semicolons == 1 and query.find(";") != len(query)-1):  # more than 1 query specified (+ last query may not have ended with ;)
            raise Exception("More than one query is written (max one allowed)")
        self.cur.execute("EXPLAIN (FORMAT JSON) " + query)
        query_plan = self.cur.fetchall()[0][0][0]["Plan"]  # extract only the plan
        return query_plan 
    
    def tokenize_query(self, query):
        '''
        Breaks query into tokens separated by whitespace
        '''
        clean_query = query.replace(",", " , ") # isolate commas
        clean_query = clean_query.replace("(", " ( ") # isolate lparen
        clean_query = clean_query.replace(")", " ) ") # isolate rparen
        clean_query = clean_query.replace(";", "") # remove semicolons
        return clean_query.split()

        
        