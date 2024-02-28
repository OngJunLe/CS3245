#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import string
import pickle

from nltk.corpus import reuters

# Format of dictionary {term: (offset, no_bytes, len_list), ...}
# Format of postings [(term, skipID), ...]

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.skip = None

    def set_next(self, node):
        self.next = node

    def set_skip(self, node):
        self.skip = node

class LinkedList:
    def __init__(self):
        self.head = None
    
    def create_posting(self, list_of_tuples):
        self.head = Node(list_of_tuples[0][0])
        current_node = self.head
        for i in range(1, len(list_of_tuples)):
            previous_node = current_node
            current_node = Node(list_of_tuples[i][0])
            previous_node.set_next(current_node)
        previous_skip_node = skip_node = self.head
        for i in range(len(list_of_tuples)):
            skip_length = list_of_tuples[i][1]
            if (skip_length != 0 and (i + skip_length) < len(list_of_tuples)): 
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

    def __len__(self):
        length = 0
        current_node = self.head
        while current_node:
            length += 1
            current_node = current_node.next
        return length

def retrieve_posting(key, dictionary, postings_file):
    offset, to_read = dictionary[key]
    postings_file.seek(offset)
    posting_list = pickle.loads(input.read(to_read))
    return posting_list

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
    memory = 0
    for fileid in reuters.fileids(): 
        if "training" in fileid:
            file_ids.append(fileid)

    for fileid in file_ids: 
        words = reuters.words(fileid)
        words = [stemmer.stem(word).lower() for word in words if word not in string.punctuation] 
        id = int(fileid.split("/")[-1])
        for word in words:
            if word in temp_postings:
                if id not in temp_postings[word]:
                    temp_postings[word].append(id)
            else:
                temp_postings[word] = [id]

        memory = sys.getsizeof(temp_postings)
        if (memory < 1000000): 
            continue
        #In process merging if size of postings dictionary exceeds 1MB
        temp_postings_keys = temp_postings.keys() 
        with open(out_postings, "rb") as input:
            for key in temp_postings_keys:
                if key in dictionary: 
                    posting_list = retrieve_posting(key, dictionary, input)
                    to_add = list(set(temp_postings[key] + posting_list))
                    postings[key] = to_add 
                else:
                    postings[key] = temp_postings[key] 
            for key in dictionary.keys():  # Adding any remaining terms in dictionary to postings
                if (key not in temp_postings_keys):
                    postings[key] = retrieve_posting(key, dictionary, input)
        temp_postings = {}
        temp_postings_keys = []
        dictionary = {}     
        sorted_keys = sorted(list(postings.keys()))   
        current_offset = 0 
        with open(out_postings, "wb") as output:
            for key in sorted_keys:
                ll_binary = pickle.dumps(postings[key])
                no_of_bytes = len(ll_binary)
                dictionary[key] = (current_offset, no_of_bytes)
                output.write(ll_binary)
                current_offset += len(ll_binary)
        postings = {}

    # Acount for anything remaining in temp_postings at end of indexing
    postings = temp_postings
    temp_postings = {}
    with open(out_postings, "rb") as input:
        for key in dictionary:
            posting_list = retrieve_posting(key, dictionary, input)
            if key in postings:    
                to_add = list(set(postings[key] + posting_list))
                postings[key] = to_add
            else:
                postings[key] = posting_list
    dictionary = {}
    sorted_keys = sorted(list(postings.keys()))   
    current_offset = 0 
    # Change all lists to list of tuples (term, skipID)
    with open(out_postings, "wb") as output:
        # Insert universal set
        universal = sorted([int(fileid.split("/")[-1]) for fileid in file_ids])
        skip_length = int(len(universal)**0.5)
        for i in range(len(universal)):
            if (i % skip_length == 0 and i != len(universal) - 1):
                universal[i] = (universal[i], skip_length)
            else:
                universal[i] = (universal[i], 0)
        universal_binary = pickle.dumps(universal)
        no_of_bytes = len(universal_binary)
        dictionary[0] = (current_offset, no_of_bytes, len(universal))
        output.write(universal_binary)
        current_offset += len(universal_binary)
        
        for key in sorted_keys:
            to_add = sorted(postings[key])
            skip_length = int(len(to_add)**0.5)
            for i in range(len(to_add)):
                if (i % skip_length == 0 and i != len(to_add) - 1):
                    to_add[i] = (to_add[i], skip_length)
                else:
                    to_add[i] = (to_add[i], 0)
            to_add_binary = pickle.dumps(to_add)
            no_of_bytes = len(to_add_binary)
            dictionary[key] = (current_offset, no_of_bytes, len(to_add))
            output.write(to_add_binary)
            current_offset += len(to_add_binary)

    dictionary_binary = pickle.dumps(dictionary)
    with open(out_dict, "wb") as output:
        output.write(dictionary_binary)


# So this doesn't run when this file is imported in other scripts
if __name__ == "__main__":
    build_index(0,"dictionary","postings")
    print('indexing over')

'''
with open("dictionary", "rb") as input:
    dictionary = pickle.loads(input.read())

with open("postings", "rb") as input:
    offset, to_read, length = dictionary["and"]
    input.seek(offset)
    posting = pickle.loads(input.read(to_read))
    print ([tuple[0] for tuple in posting])
# Answer for 20: [1, 10, 100, 1000, 10005, 10011, 10014, 10015, 10018, 10023]

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
