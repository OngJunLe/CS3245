This is the README file for A0216276A's, A0291640H's submission 
Email(s): e0538377@u.nus.edu, e1332814@u.nus.edu

== Python Version ==

We're using Python Version 3.11.2 for this assignment.

== General Notes about this assignment ==
The Reuters corpus was accessed via API with reuters.words(), with the search terms being the file names in the specified in_dir appended to "training" since it was specified that we would be using the training set only e.g. "training/1".

build_index() in index.py follows the SPIMI logic taught in lectures, with terms and DocIDs hashed into the postings dictionary in memory, and then written to disk as postings.txt whenever this dictionary exceeds an arbitrary 2MB in size. Merging is also done during this writing process so that there are only ever 2 existing blocks: the postings dictionary in memory, as well as the previous postings dictionaries that have been merged and written to disk. During the merging process, each posting list for a term in memory is merged with the matching posting list for the same term on disk if it exists; the posting lists are read in one at a time, and processed terms are removed from the postings dictionary in memory so that the memory limit is not exceeded. 2 files are outputted: dictionary.txt, with a dictionary of (term, (byte offset of posting list in postings.txt, number of bytes of postings list, length of postings list)), and postings.txt, with posting lists of tuples (DocID, Skip Length), both serialised with Pickle. The byte offset approach ensures that postings lists can be read in search.py without reading the entire postings.txt.

QueryProcessor (defined in query_processor.py) does the following to a given string query: -split the string into a list of tokens of operators/terms -optimise the query -remove trivial operations e.g. a AND NOT a -rearrange the terms so the terms with shorter postings lists are evaluated first -convert the order of tokens to be in postfix notation -evaluate the query, loading the linkedlists from disk as needed

search.py applies QueryProcessor.process_query() to all the lines in queries.txt, and writes them to output.txt

== Files included with this submission == 
index.py: Code for indexing logic.
search.py: Code for search logic. 
query_processor.py: Helper class for processing search. 
dictionary.txt: Dictionary serialised with Pickle. 
postings.txt: Posting lists serialised with Pickle.

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[ x ] We, A0216276A and A0291640H, certify that we have followed the CS 3245 Information Retrieval class guidelines for homework assignments. In particular, we expressly vow that we have followed the Facebook rule in discussing with others in doing the assignment and did not take notes (digital or printed) from the discussions.

[ ] I/We, A0000000X, did not follow the class rules regarding homework assignment, because of the following reason:

We suggest that we should be graded as follows:

== References ==

<Please list any websites and/or people you consulted with for this assignment and state their role> https://stackoverflow.com/questions/14529523/python-split-for-lists - how to split list by a term.

https://en.wikipedia.org/wiki/Shunting_yard_algorithm - logic for shunting yard algorithm.

https://www.geeksforgeeks.org/evaluation-of-postfix-expression/ - logic for evaluating postfix expression.