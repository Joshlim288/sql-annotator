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
        self.other_operators = {}

    def annotate(self, query_plan):
        self.scans_dict = {}
        self.joins_arr = []

        self.add_annotations(query_plan)
        print("Scans:")
        print(self.scans_dict)
        print("Joins:")
        print(self.joins_arr)

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

            annotator(curr_plan)

    """ Methods to handle each node type """
    def nested_loop(self, plan):
        """
        Each nested loop node type has an array Plans of size 2.
        """
        self.joins_arr.append("This join is performed using a Nested Loop")

    def hash_join(self, plan):
        self.joins_arr.append("This join is performed using a Hash Join")

    def merge_join(self, plan):
        self.joins_arr.append("This join is performed using a Merge Join")

    def seq_scan(self, plan):
        annotation = "This table is read using a sequential scan."
        if "Filter" in plan:
            annotation += f" The filter {plan['Filter'][1:-1]} is applied."
        self.scans_dict[plan["Alias"]] = annotation
        # alias = ""
        # if plan["Alias"] != plan["Relation Name"]:
        #     alias = f" ({plan['Alias']})"
        #
        # annotation = f"Table {plan['Relation Name']}{alias} is read using a sequential scan"
        # if "Filter" in plan:
        #     annotation += f" with selection '{plan['Filter'][1:-1]}'"
        # if "Parent Relationship" in plan:
        #     annotation += f". This is the {plan['Parent Relationship']} table in the parent join"

    def index_scan(self, plan):
        annotation = "This table is read using an index scan."
        if "Index Cond" in plan:
            annotation += f" The index condition is {plan['Index Cond'][1:-1]}."
        self.scans_dict[plan["Alias"]] = annotation
        pass

    def index_only_scan(self):
        pass

    def bitmap_index_scan(self):
        pass

    def bitmap_heap_scan(self):
        pass

    def sample_scan(self):
        pass

    def tid_scan(self):
        pass

    def tid_range_scan(self):
        pass

    def subquery_scan(self):
        pass

    def function_scan(self):
        pass

    def table_function_scan(self):
        pass

    def values_scan(self):
        pass

    def cte_scan(self):
        pass

    def named_tuplestore_scan(self):
        pass

    def worktable_scan(self):
        pass

    def foreign_scan(self):
        pass

    def custom_scan(self):
        pass

    def result(self):
        pass

    def project_set(self):
        pass

    def modify_table(self):
        pass

    def append(self):
        pass

    def merge_append(self):
        pass

    def recursive_union(self):
        pass

    def bitmap_and(self):
        pass

    def bitmap_or(self):
        pass

    def gather(self):
        pass

    def gather_merge(self):
        pass

    def materialize(self):
        pass

    def memoize(self):
        pass

    def sort(self):
        pass

    def incremental_sort(self):
        pass

    def group(self):
        pass

    def aggregate(self):
        pass

    def window_agg(self):
        pass

    def unique(self):
        pass

    def set_op(self):
        pass

    def lock_rows(self):
        pass

    def limit(self):
        pass

    def hash(self):
        pass