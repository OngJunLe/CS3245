from query_processor import QueryProcessor
from index import LinkedList, Node # used by QueryProcessor
import dask.distributed as dd
import os
import time

class SearchEngine:
    def __init__(self, query_processor):
        self.query_processor = query_processor

    def process_query_file(self, query_file, output_file):
        # set up dask client
        no_cores = len(os.sched_getaffinity(0))
        print(f"using {no_cores} cores")
        client = dd.Client(n_workers=no_cores, threads_per_worker=1)

        # read queries from file
        with open(query_file, 'r') as f:
            queries = f.readlines()      

        # process queries in parallel
        # results = client.map(self.query_processor.process_query, queries)
        # result_strings = []
        # for result in client.gather(results):
        #     result_strings.append(str(result))

        result_strings_future = client.map(self.query_processor.process_query, queries)
        result_strings = client.gather(result_strings_future)

            # result_strings = []
            # for query in queries:
            #     result = self.query_processor.process_query(query)
            #     result_strings.append(str(result))
        
        # write results to output file
        with open(output_file, 'w') as f:
            f.write('\n'.join(result_strings))

        print(f'output written to {output_file}')

if __name__ == "__main__":

    start = time.time()

    qp = QueryProcessor('./dictionary', './postings')
    se = SearchEngine(qp)

    se.process_query_file('./queries.txt', './output.txt')

    end = time.time()

    print(f"script took {end-start} seconds")