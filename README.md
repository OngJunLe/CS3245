This is the README file for A0216276A's, <ADD STUDENT ID HERE> submission
Email(s): e0538377@u.nus.edu, <ADD EMAIL HERE>

== Python Version ==

We're using Python Version 3.11.2 for
this assignment.

== General Notes about this assignment ==

build_index() in index.py closely follows the SPIMI logic taught in lectures, with terms and DocIDs hashed into the postings dictionary in memory, and then written to disk whenever the dictionary exceeds an arbitrary 1MB in size. Merging is also done during this writing process so that there are only ever 2 existing blocks: the postings dictionary in memory, as well as the previous postings dictionaries that have been merged and written to disk. 2 files are outputted: dictionary.txt, with a dictionary of (term, (byte offset of posting list in postings.txt, number of bytes of postings list, length of postings list)) serialised with Pickle, and postings.txt, with posting lists of tuples (DocID, Skip Length) serialised with Pickle. 
The Reuters corpus was accessed via API with reuters.fileids() and reuters.words() rather than directory.

== Files included with this submission ==
<RENAME DICTIONARY AND POSTINGS BEFORE SUBMISSION>
index.py: Code for indexing logic
search.py: Code for search logic
query_processor.py: Helper class for processing search
dictionary.txt: Dictionary serialised with Pickle.
postings.txt: Posting lists serialised with Pickle. 

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[ x ] We, A0216276A and <ADD STUDENT ID HERE>, certify that we have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, we
expressly vow that we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] I/We, A0000000X, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

We suggest that we should be graded as follows:

<Please fill in>

== References ==

<Please list any websites and/or people you consulted with for this
assignment and state their role>
