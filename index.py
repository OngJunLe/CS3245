#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import string
import pickle

from nltk.corpus import reuters

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.skip = None

    def set_next(self, node):
        self.next = node

    def set_skip(self, node):
        self.skip = node

class linked_list:
    def __init__(self):
        self.head = None
    
    def create_posting(self, list):
        self.head = Node(list[0])
        current_node = self.head
        skip_length = (len(list) - 1)**0.5
        for i in range(1, len(list)):
            previous_node = current_node
            current_node = Node(list[i])
            previous_node.set_next(current_node)
        previous_skip_node = skip_node = self.head
        for i in range(int(skip_length)):
            for j in range(int(skip_length)):
                skip_node = skip_node.next
            previous_skip_node.set_skip(skip_node)
            previous_skip_node = skip_node


    # defines what happens when you run str() on this
    def __str__(self):
        current_node = self.head
        output = ""
        while current_node:
            output += str(current_node.data)
            if current_node.next:
                output += " "
            current_node = current_node.next
        return output


def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d temp_postings-file -p postings-file")

def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the temp_postings file and postings file
    """
    print('indexing...')
    # This is an empty method
    # Pls implement your code in below
    file_ids = []
    temp_postings = {} 
    postings = {} 
    dictionary = {}
    stemmer = nltk.stem.PorterStemmer()
    for fileid in reuters.fileids(): # Rework when dealing with all data rather than subset
        if "training" in fileid:
            file_ids.append(fileid)
    for fileid in file_ids[:10]:
        words = reuters.words(fileid)
        words = [stemmer.stem(word).lower() for word in words if word not in string.punctuation] 
        id = int(fileid.split("/")[-1])
        while True: # Account for memory overflow later 
            for word in words:
                if word in temp_postings:
                    if id not in temp_postings[word]:
                        temp_postings[word].append(id)
                else:
                    temp_postings[word] = [id]
            break
        # Merge logic - implement merging only when memory overflow later 
        temp_postings_keys = temp_postings.keys() 
        for key in temp_postings_keys:
            if key in postings:
                to_add = set(temp_postings[key]) - set(postings[key])
                postings[key] += list(to_add)
            else:
                postings[key] = temp_postings[key]

    # Write postings and dictionary to disk            
    sorted_keys = sorted(list(postings.keys()))   
    current_offset = 0 
    output = open(out_postings, "wb")
    for key in sorted_keys:
        ll = linked_list()
        ll.create_posting(postings[key])
        ll_binary = pickle.dumps(ll)
        no_of_bytes = len(ll_binary)
        dictionary[key] = (current_offset, no_of_bytes)
        output.write(ll_binary)
        current_offset += len(ll_binary)
    output.close()

    output = open(out_dict, "wb")
    dictionary_binary = pickle.dumps(dictionary)
    output.write(dictionary_binary)
    output.close()

# so this doesn't run when this file is imported in other scripts
if __name__ == "__main__":
    build_index(0,"dictionary","postings")

'''
try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # temp_postings file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
'''
