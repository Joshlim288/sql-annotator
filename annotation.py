class Annotator:

    def __init__(self):
        self.annotations = []

    def annotate(self, query_plan):
        self.annotations = []
        pass

    """ Methods to handle each node type """
    def nested_loop(self):
        """
        Each nested loop node type has an array Plans of size 2.
        Nested loops have to be analyzed bottom-up
        """

        pass

    def hash_join(self):
        pass

    def merge_join(self):
        pass

    def seq_scan(self):
        pass

    def index_scan(self):
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
