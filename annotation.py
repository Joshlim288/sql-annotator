import re
from collections import OrderedDict
class Annotator:

    def __init__(self):
        self.join_operators = ["Nested Loop", "Hash Join", "Merge Join"]
        self.scan_operators = [
            "Seq Scan", "Index Scan", "Index Only Scan", "Bitmap Index Scan", "Sample Scan", "Tid Scan", "Tid Range Scan", 
            "Subquery Scan", "Function Scan", "Table Function Scan", "Values Scan", "CTE Scan", "Named Tuplestore Scan", 
            "WorkTable Scan", "Foreign Scan", "Custom Scan"
        ]
        self.other_operators = {
            "Sort": self.sort,
            "Incremental Sort": self.incremental_sort,
            "Aggregate": self.aggregate,
            "GroupAggregate": self.groupaggregate,
            "HashAggregate": self.hashaggregate,
        }

        # SQL keywords to look out for
        self.sql_keywords = ["FROM", "SELECT", "ORDER", "GROUP", "UPDATE", "DELETE"]
        self.aggregates = ("AVG", "COUNT", "MAX", "MIN", "SUM")  # need to be a tuple to use 'in'

    def annotate(self, query_plan, tokenized_query):
        self.scans_dict = {}
        self.joins_arr = []
        self.aggregates_arr = []
        self.sorts_arr = []
        self.subplans_arr = []
        self.annotations_dict = {}

        self.prepare_annotations(query_plan)
        self.attach_annotations(tokenized_query)
        self.annotations_dict["cost"] = "Total cost of the query plan is: " + str([query_plan][0]["Total Cost"]) + "."

        ordered = OrderedDict()  # order annotations by token id
        token_ids = list(self.annotations_dict.keys())
        token_ids.remove("cost")  # not involved in sorting
        sort_key = lambda x: x if type(x) != tuple else x[0]  # if token_id is a tuple, then we compare using the 1st element of the tuple
        for token_id in sorted(token_ids, key=sort_key):
            ordered[token_id] = self.annotations_dict[token_id]
        ordered["cost"] = self.annotations_dict["cost"]
        return ordered

    def prepare_annotations(self, query_plan):
        """
        Use DFS to prepare annotations for individual plans.
        """
        queue = [query_plan]
        while len(queue) != 0:
            curr_plan = queue.pop(0)
            if "Plans" in curr_plan:  # this operator has child operations
                for i in range(len(curr_plan["Plans"])):
                    queue.insert(0, curr_plan["Plans"][len(curr_plan["Plans"]) - 1 - i]) # insert in reverse order, so first subplan is examined first

            if "Subplan Name" in curr_plan:  # this plan creates a subplan
                subplan_name = curr_plan["Subplan Name"]
                match = re.search("\$\d+", subplan_name)
                if match:  
                    # if match, subplan_name is e.g. "InitPlan 1 (returns $1)". Extract $1
                    # if no match, subplan_name is e.g. "SubPlan 1". Do nothing
                    subplan_name = match.group(0)

                if "One-Time Filter" in curr_plan:  # add one-time filter condition
                    self.subplans_arr.append({"name": subplan_name, "otf": curr_plan['One-Time Filter']})
                else:
                    self.subplans_arr.append({"name": subplan_name})

            # add annotations for curr_plan
            node_type = curr_plan["Node Type"]
            if node_type in self.join_operators:
                self.handle_joins(curr_plan)
            elif node_type in self.scan_operators:
                self.handle_scans(curr_plan)
            elif node_type in self.other_operators:
                self.other_operators[node_type](curr_plan)
            else:
                continue
        
    def attach_annotations(self, tokenized_query):
        """
        Attaches the annotations for joins to their respective FROM clauses
        """
        brackets_stack = []  # for tracking (closed) brackets
        brackets_arr = []  # array of [index, index] 
        appeared_tables = {}  # dict of {table: count}. Possible for same table (without alias) to appear multiple times in a query
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
                    # need to check if we are attaching annotations to repeated table name without alias
                    if token not in appeared_tables.keys():
                        annotation = self.scans_dict[token] # annotate current token with it's related scan annotation
                        appeared_tables[token] = 1
                    else:  # table name appeared twice - find postgres-added alias
                        annotation = self.scans_dict[f"{token}_{appeared_tables[token]}"]  # postgres will add a counter to the (repeated) table name
                        appeared_tables[token] += 1
                    # attach annotations
                    annotation_text = f"The table \"{annotation['name']}\"{annotation['alias']} is read using a {annotation['scan_type']}."
                    if "filter" in annotation.keys():
                        annotation_text += f" The filter \"{annotation['filter']}\" is applied."
                    elif "cond" in annotation.keys():
                        annotation_text += f" The index condition \"{annotation['cond']}\" is applied."
                    self.annotations_dict[i] = annotation_text

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
                # we need to make sure still can attach annotation to group by if it's the last clause
                if (token.upper() in self.sql_keywords or i == len(tokenized_query)-1) and len(self.sorts_arr) != 0: # Finish annotation for the GROUP BY clause
                    if (tokenized_query[clause_index+1].upper() == "BY"):  # attach annotation to both group/order and by
                        self.annotations_dict[(clause_index, clause_index+1)] = self.sorts_arr.pop(0)
                    else:
                        raise Exception("Found GROUP/ORDER without BY")
            
            elif current_clause == "UPDATE" or current_clause == "DELETE":  # for these, just attach scans, if any
                if token in self.scans_dict.keys():
                    self.annotations_dict[i] = self.scans_dict[token] # annotate current token with it's related scan annotation
                    
            if token.upper() in self.sql_keywords:
                current_clause = token.upper()
                clause_index = i
            else:  # track queries within a bracket
                if token == '(':
                    brackets_stack.append(i)
                elif token == ')':  # close an open bracket
                    open_bracket = brackets_stack.pop()
                    brackets_arr.append((open_bracket, i))
            i += 1
        
        # annotate brackets
        while len(brackets_arr) != 0 and len(self.subplans_arr) != 0:
            bracket = brackets_arr.pop()  # outer most bracket is the 1st subplan
            subplan = self.subplans_arr.pop(0)
            annotation = f"Results of this group are stored in \"{subplan['name']}\"."
            if "otf" in subplan:
                annotation += f" A One-Time Filter \"{subplan['otf'][1:-1]}\" is applied."
            self.annotations_dict[bracket] = annotation

    """ Methods to handle each node type """
    def handle_joins(self, plan):
        for key in plan.keys():
            if "cond" in key.lower():
                conds = plan[key].strip('()').split(' ') 
                self.joins_arr.append({
                        "name": plan["Node Type"] + " with condition: \"" + re.sub('[()]', '', plan[key]) + "\"", 
                        "conds": [conds[0], conds[-1]] # ignore operators
                    })
                return

        self.joins_arr.append({
                        "name": plan["Node Type"], 
                        "conds": []
                    })

    def __get_alias(self, plan):  # helper method to return alias of a table, if it exists
        alias = ""
        if plan["Alias"] != plan["Relation Name"]:
            alias = f" (alias \"{plan['Alias']}\")"

        return alias

    def handle_scans(self, plan):
        annotation = {}
        annotation["scan_type"] = plan["Node Type"]
        annotation["name"] = plan["Relation Name"]
        annotation["alias"] = self.__get_alias(plan)
        if "Filter" in plan:
            annotation["filter"] = plan['Filter'][1:-1]
        elif "Index Cond" in plan:
            annotation["cond"] = plan['Index Cond'][1:-1]
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

    def groupaggregate(self, plan):
        annotation = f"This aggregation is performed using GroupAggregate and with the strategy \"{plan['Strategy']}\"."
        if "Filter" in plan:
            annotation += f" The filter \"{plan['Filter']}\" is applied."
        self.aggregates_arr.append(annotation)

    def hashaggregate(self, plan):
        annotation = f"This aggregation is performed using HashAggregate and with the strategy \"{plan['Strategy']}\"."
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