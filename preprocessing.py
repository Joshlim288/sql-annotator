import re
import psycopg2

# class to handle query pre-processing:
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
        conn.autocommit = True
        self.cur = conn.cursor()

    def process_query(self, query):
        '''
        Retrieves query plan from Postgresql
        :param query: query to be analyzed
        :returns: query_plan if query is valid
        '''
        self.cur.execute("EXPLAIN (FORMAT JSON) " + query)
        query_plan = self.cur.fetchall()[0][0][0]["Plan"]  # extract only the plan
        return query_plan 
    
    def tokenize_query(self, query):
        clean_query = query.replace(",", " , ") # isolate commas
        clean_query = clean_query.replace("(", " ( ") # isolate lparen
        clean_query = clean_query.replace(")", " ) ") # isolate rparen
        return clean_query.split()

        
        