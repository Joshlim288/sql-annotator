import re
class Annotator:

    def __init__(self):
        self.annotations = []
        self.join_operators = {  # map join node types to their functions
            "Nested Loop": self.nested_loop,
            "Hash Join": self.hash_join,
            "Merge Join": self.merge_join,
        }
        self.scan_operators = {  # map scan node types to their functions
            "Seq Scan": self.seq_scan,
            "Index Scan": self.index_scan,
            "Index Only Scan": self.index_only_scan,
            "Bitmap Index Scan": self.bitmap_index_scan,
            "Sample Scan": self.sample_scan,
            "Tid Scan": self.tid_scan,
            "Tid Range Scan": self.tid_range_scan,
            "Subquery Scan": self.subquery_scan,
            "Function Scan": self.function_scan,
            "Table Function Scan": self.table_function_scan,
            "Values Scan": self.values_scan,
            "CTE Scan": self.cte_scan,
            "Named Tuplestore Scan": self.named_tuplestore_scan,
            "WorkTable Scan": self.worktable_scan,
            "Foreign Scan": self.foreign_scan,
            "Custom Scan": self.custom_scan,
        }
        self.other_operators = {
            "Sort": self.sort,
            "Incremental Sort": self.incremental_sort,
            "Aggregate": self.aggregate,
        }

        # SQL keywords to look out for
        self.sql_keywords = ["FROM", "SELECT", "ORDER", "GROUP", "UPDATE", "DELETE"]
        self.aggregates = ("AVG", "COUNT", "MAX", "MIN", "SUM")  # need to be a tuple to use 'in'
        

    def annotate(self, query_plan, tokenized_query):
        self.scans_dict = {}
        self.joins_arr = []
        self.aggregates_arr = []
        self.sorts_arr = []
        self.annotations_dict = {}

        self.add_annotations(query_plan)
        self.attach_annotations(tokenized_query)
        return self.annotations_dict

    def add_annotations(self, query_plan):
        """
        Use BFS to apply annotations to individual plans.
        BFS is used so that we can map the first "From" to the first Join operation
        :param query_plan:
        :return:
        """
        queue = [query_plan]
        while len(queue) != 0:
            curr_plan = queue.pop(0)
            if "Plans" in curr_plan:  # this operator has child operations
                for plan in curr_plan["Plans"]:
                    queue.append(plan)

            # add annotations for curr_plan
            node_type = curr_plan["Node Type"]
            annotator = None
            if node_type in self.join_operators:
                annotator = self.join_operators[node_type]
            elif node_type in self.scan_operators:
                annotator = self.scan_operators[node_type]
            elif node_type in self.other_operators:
                annotator = self.other_operators[node_type]
            else:
                # raise Exception("Invalid Node Type Found:", node_type)
                continue
            if annotator:
                annotator(curr_plan)
        
    def attach_annotations(self, tokenized_query):
        """
        Attaches the annotations for joins to their respective FROM clauses
        """
        self.annotations_dict = {}
        current_clause = tokenized_query[0].upper()
        table_counter = 0
        clause_index = 0
        i = 0
        while i < len(tokenized_query):
            token = tokenized_query[i]
            if current_clause == "FROM": # inside a FROM clause
                if (token.upper() in self.sql_keywords or i == len(tokenized_query)-1): # Finish annotation for the FROM clause
                    current_clause = token.upper()
                    table_counter = 0
                    if clause_index in self.annotations_dict.keys():
                        self.annotations_dict[clause_index] = "This join is carried out with a " + self.annotations_dict[clause_index] + "."

                elif token in self.scans_dict.keys(): # attach scans to the index of their alias names within FROM clause
                    self.annotations_dict[i] = self.scans_dict[token] # annotate current token with it's related scan annotation
                    if table_counter == 1: # If 2 tables in the from clause, annotate it with a join
                        self.annotations_dict[clause_index] = self.joins_arr.pop(0)["name"]
                    elif table_counter > 1: # If more than 2 tables in the from clause, annotate with a join for each
                        self.annotations_dict[clause_index] = self.joins_arr.pop(0)["name"] + ", followed by a " + self.annotations_dict[clause_index]
                    table_counter += 1
                
                if len(self.joins_arr) > 0:
                    for condName in self.joins_arr[0]["conds"]:
                        if (condName in token and table_counter == 1): # if part of a condition is found in a where clause and only one table in the from clause
                            self.annotations_dict[clause_index] = self.joins_arr.pop(0)["name"]
                            break


            elif current_clause == "SELECT":  # attach aggregate annotations
                if token.upper() in self.sql_keywords: # Finish annotation for the SELECT clause
                    current_clause = token.upper()
                    for j in range(clause_index, i):  
                        # check if tokens from the SELECT clause to this current token are aggregate functions
                        # if so, attach them
                        if tokenized_query[j].upper().startswith(self.aggregates):
                            self.annotations_dict[j] = self.aggregates_arr.pop(0)

            elif current_clause == "GROUP" or current_clause == "ORDER":  # attach sort annotations
                # group by has priority over order by - so if both appear together, order by may not have any sorts to attach to
                # group by may also appear without requiring any sorting to be performed
                if (token.upper() in self.sql_keywords or i == len(tokenized_query)-1) and len(self.sorts_arr) != 0: # Finish annotation for the GROUP BY clause
                    # need to make sure still can attach annotation to group by if it's the last clause
                    self.annotations_dict[clause_index] = self.sorts_arr.pop(0)
            
            elif current_clause == "UPDATE" or current_clause == "DELETE":  # for these, just attach scans, if any
                if token in self.scans_dict.keys():
                    self.annotations_dict[i] = self.scans_dict[token] # annotate current token with it's related scan annotation
                    
            if (token.upper() in self.sql_keywords):
                current_clause = token.upper()
                clause_index = i

            i += 1


    """ Methods to handle each node type """
    """ Joins """
    def nested_loop(self, plan):
        """
        Each nested loop node type has an array Plans of size 2.
        """
        for key in plan.keys():
            if "cond" in key.lower():
                conds = plan[key].strip('()').split(' ') 
                self.joins_arr.append({
                        "name": "Nested Loop Join", 
                        "conds": [conds[0], conds[-1]] # ignore operators
                    })
                return

        self.joins_arr.append({
                        "name": "Nested Loop Join", 
                        "conds": []
                    })

    def hash_join(self, plan):
        for key in plan.keys():
            if "cond" in key.lower():
                conds = plan[key].strip('()').split(' ') 
                self.joins_arr.append({
                        "name": "Hash Join", 
                        "conds": [conds[0], conds[-1]] # ignore operators
                    })
                return

        self.joins_arr.append({
                        "name": "Hash Join", 
                        "conds": []
                    })

    def merge_join(self, plan):
        for key in plan.keys():
            if "cond" in key.lower():
                conds = plan[key].strip('()').split(' ') 
                self.joins_arr.append({
                        "name": "Merge Join", 
                        "conds": [conds[0], conds[-1]] # ignore operators
                    })
                return

        self.joins_arr.append({
                        "name": "Merge Join", 
                        "conds": []
                    })

    """ Scans """
    def __get_alias(self, plan):  # helper method to return alias of a table, if it exists
        alias = ""
        if plan["Alias"] != plan["Relation Name"]:
            alias = f" (alias \"{plan['Alias']}\")"

        return alias

    def seq_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Sequential Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def index_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using an Index Scan."
        if "Index Cond" in plan:
            annotation += f" The index condition is \"{plan['Index Cond'][1:-1]}\"."
        self.scans_dict[plan["Alias"]] = annotation

    def index_only_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using an Index Only Scan."
        if "Index Cond" in plan:
            annotation += f" The index condition is \"{plan['Index Cond'][1:-1]}\"."
        self.scans_dict[plan["Alias"]] = annotation

    def bitmap_index_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Bitmap Index Scan."
        if "Index Cond" in plan:
            annotation += f" The index condition is \"{plan['Index Cond'][1:-1]}\"."
        self.scans_dict[plan["Alias"]] = annotation

    def bitmap_heap_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Bitmap Heap Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def sample_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Sample Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def tid_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Tid Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def tid_range_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Tid Range Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def subquery_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Subquery Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def function_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Function Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def table_function_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Table Function Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def values_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Values Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def cte_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a CTE Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def named_tuplestore_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Named Tuplestore Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def worktable_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Worktable Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def foreign_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Foreign Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    def custom_scan(self, plan):
        alias = self.__get_alias(plan)
        
        annotation = f"The table \"{plan['Relation Name']}\"{alias} is read using a Custom Scan."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter'][1:-1]}\" is applied."
        self.scans_dict[plan["Alias"]] = annotation

    """ Other Nodes """
    def result(self, plan):
        pass

    def project_set(self, plan):
        pass

    def modify_table(self, plan):
        pass

    def append(self, plan):
        pass

    def merge_append(self, plan):
        pass

    def recursive_union(self, plan):
        pass

    def bitmap_and(self, plan):
        pass

    def bitmap_or(self, plan):
        pass

    def gather(self, plan):
        pass

    def gather_merge(self, plan):
        pass

    def materialize(self, plan):
        pass

    def memoize(self, plan):
        pass

    def sort(self, plan):
        annotation = f"This sort is performed with sort key(s) \"{', '.join(plan['Sort Key'])}\"."
        if "Sort Method" in plan:
            annotation += f" The sort method is \"{plan['Sort Method']}\"."
        self.sorts_arr.append(annotation)

    def incremental_sort(self, plan):
        annotation = f"This sort is performed with sort key(s) \"{', '.join(plan['Sort Key'])}\"."
        if "Sort Method" in plan:
            annotation += f" The sort method is \"{plan['Sort Method']}\"."
        self.sorts_arr.append(annotation)

    def group(self, plan):
        pass

    def aggregate(self, plan):
        annotation = f"This aggregation is performed with the strategy \"{plan['Strategy']}\"."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter']}\" is applied."
        self.aggregates_arr.append(annotation)

    def window_agg(self, plan):
        pass

    def unique(self, plan):
        pass

    def set_op(self, plan):
        pass

    def lock_rows(self, plan):
        pass

    def limit(self, plan):
        pass

    def hash(self, plan):
        pass