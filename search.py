#!/usr/bin/python3
from query_processor import QueryProcessor
from index import LinkedList, Node # used by QueryProcessor
import re
import nltk
import sys
import getopt

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

class SearchEngine:
    def __init__(self, query_processor):
        self.query_processor = query_processor

    def process_query_file(self, query_file, output_file):
        # read queries from file
        with open(query_file, 'r') as f:
            queries = f.readlines()  

        result_strings = []
        for q in queries:
            result_strings.append(self.query_processor.process_query(q))
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(result_strings))
        
        print(f'output written to {output_file}')

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')

    qp = QueryProcessor(dict_file, postings_file)
    se = SearchEngine(qp)
    se.process_query_file(queries_file, results_file)

dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
