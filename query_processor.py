import re
import pickle
from index import LinkedList, Node
from nltk.stem import PorterStemmer
from itertools import groupby
import traceback

# efficiency stuff
# demorgans law
# for operations of same priority, do the ones for lists with the least number of elements first
# contradiction check e.g. a AND NOT a

class QueryProcessor:
    OPERATOR_OR = 1
    OPERATOR_AND = 2
    OPERATOR_NOT = 3
    LOGICAL_OPERATORS = [OPERATOR_OR, OPERATOR_AND, OPERATOR_NOT]
    # OPERATOR_FUNCTION = {OPERATOR_OR: or_operation, OPERATOR_AND: and_operation, OPERATOR_NOT: not_operation}

    LEFT_PARENTHESIS = 0
    RIGHT_PARENTHESIS = -1
    OPERATOR_LIST = [OPERATOR_OR, OPERATOR_AND, OPERATOR_NOT, LEFT_PARENTHESIS, RIGHT_PARENTHESIS]

    regex_pattern = r'\bAND\b|\bOR\b|\bNOT\b|[\(\)]|[^\s()]+'
    #regex_pattern = r'\bAND\b|\bOR\b|\bNOT\b|[\(\)]|\w+'

    def __init__(self, dictionary_file, postings_file):
        self.dictionary_file = dictionary_file
        self.postings_file = postings_file
        self.stemmer = PorterStemmer()
        #self.output_file = output_file
        
        with open(dictionary_file, 'rb') as f:
            self.dictionary = pickle.load(f)

        # add empty set
        self.dictionary[LinkedList.EMPTY_SET_KEY] = (0, 0, 0)

        pass

    def process_query(self, query):
        try:
            tokens = list(self.tokenize_query(query))

            # check for any invalid tokens and phrase queries
            invalid_tokens = []
            prev_token_is_term = False
            for t in tokens:
                if t in self.dictionary:
                    if prev_token_is_term:
                        return "phrase query detected, please ensure all terms all separated by operators"
                    elif "&" in t or "|" in t or "~" in t:
                        invalid_tokens.append(t)
                    prev_token_is_term = True
                else:
                    prev_token_is_term = False
                    if t not in self.OPERATOR_LIST:
                        invalid_tokens.append(t)

            if len(invalid_tokens) > 0:
                return "invalid token(s): " + ", ".join(invalid_tokens)

            tokens = self.optimise_query(tokens)
            
            if len(tokens) == 0: return ""

            postfix = self.convert_to_postfix(tokens)

            result = self.evaluate_postfix(postfix)
            
        except Exception as e:
            return "ERROR" + traceback.format_exc()
        
        return str(result)
    
    def optimise_query(self, tokens):

        # could have integrated remove_trivial_expressions with rearrange_query, would have allowed for handling trivial expressions with OR

        # remove trivial expressions e.g. a AND NOT a
        tokens = self.remove_trivial_expressions(tokens)

        # convert subsets of list between parentheses into sublists
        tokens = self.process_parentheses(tokens)

        # rearrange the query to process terms with the shortest postings list first
        tokens = self.rearrange_query(tokens)

        return tokens

    def tokenize_query(self, query):
        for token in re.findall(self.regex_pattern, query):
            if token == "AND":
                yield self.OPERATOR_AND
            elif token == "OR":
                yield self.OPERATOR_OR
            elif token == "NOT":
                yield self.OPERATOR_NOT
            elif token == "(":  
                yield self.LEFT_PARENTHESIS
            elif token == ")":
                yield self.RIGHT_PARENTHESIS
            else:
                yield self.stemmer.stem(token).lower()
        
    def convert_to_postfix(self, tokens):
        output_queue = []
        operator_stack = []

        for token in tokens:
            # token = next(tokens)
            if token in self.LOGICAL_OPERATORS:
                while (operator_stack and operator_stack[-1] >= token): # OR AND NOT will never be greater than parenthesis, omit check for parenthesis
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)
            elif token == self.LEFT_PARENTHESIS:
                operator_stack.append(token)
            elif token == self.RIGHT_PARENTHESIS:
                while operator_stack and operator_stack[-1] != self.LEFT_PARENTHESIS:
                    output_queue.append(operator_stack.pop())
                if not operator_stack:
                    raise ValueError("missing left parenthesis")
                operator_stack.pop() # remove the left parenthesis
            else: # token is a term
                output_queue.append(token)

        while operator_stack:
            if operator_stack[-1] in [self.LEFT_PARENTHESIS, self.RIGHT_PARENTHESIS]:
                raise ValueError("mismatched parenthesis")
            output_queue.append(operator_stack.pop())

        return output_queue

    def remove_trivial_expressions(self, tokens):

        # remove a AND NOT a, a AND UNIVERSAL_SET, a AND EMPTY_SET, a AND a
        change = True
        while change:
            change = False
            for i in range(len(tokens)-3,-1,-1):
                if tokens[i+1] == self.OPERATOR_AND:
                    if i+3 < len(tokens) and tokens[i] not in self.OPERATOR_LIST and tokens[i] == tokens[i+3] and tokens[i+2] == self.OPERATOR_NOT: # a AND NOT a
                        tokens[i:i+4] = [LinkedList.EMPTY_SET_KEY]
                        change = True
                    elif tokens[i] == LinkedList.UNIVERSAL_SET_KEY or tokens[i+2] == LinkedList.UNIVERSAL_SET_KEY or tokens[i+2] == tokens[i]: # a AND UNIVERSAL_SET, UNIVERSAL_SET AND a, a AND a
                        tokens[i:i+3] = [tokens[i]]
                        change = True
                    elif tokens[i] == LinkedList.EMPTY_SET_KEY or tokens[i+2] == LinkedList.EMPTY_SET_KEY: # a AND EMPTY_SET, EMPTY_SET AND a
                        tokens[i:i+3] = [LinkedList.EMPTY_SET_KEY]
                        change = True

        # this doesn't work because AND takes precedence over OR, could be a OR NOT a AND b 
        # remove a OR NOT a, a OR NOT a, a OR EMPTY_SET, a OR a,  a OR UNIVERSAL_SET
        # change = True
        # while change:
        #     change = False
        #     for i in range(len(tokens)-4,-1,-1):
        #         if tokens[i+1] == self.OPERATOR_OR:
        #             if tokens[i] not in self.OPERATOR_LIST and tokens[i] == tokens[i+3] and tokens[i+2] == self.OPERATOR_NOT: # a OR NOT a 
        #                 tokens[i:i+4] = [LinkedList.UNIVERSAL_SET_KEY]
        #             if tokens[i] == LinkedList.EMPTY_SET_KEY or tokens[i+2] == LinkedList.EMPTY_SET_KEY or tokens[i+2] == tokens[i]:
        #                 tokens[i:i+3] = [tokens[i]]
        #             if tokens[i+1] == self.OPERATOR_OR and (tokens[i+2] == LinkedList.EMPTY_SET_KEY or tokens[i+2] == tokens[i]):
        #                 tokens[i:i+3] = [tokens[i]]
        #             if tokens[i+1] == self.OPERATOR_OR and tokens[i+2] == LinkedList.UNIVERSAL_SET_KEY:
        #                 tokens[i:i+3] = [LinkedList.UNIVERSAL_SET_KEY]

        # de morgan's law, for NOT a AND NOT b => NOT (a OR b)
        for i in range(len(tokens)-5,-1,-1):
            if tokens[i] == self.OPERATOR_NOT and tokens[i+1] not in self.OPERATOR_LIST and tokens[i+2] == self.OPERATOR_AND and tokens[i+3] == self.OPERATOR_NOT and tokens[i+4] not in self.OPERATOR_LIST:
                tokens[i:i+5] = [self.OPERATOR_NOT, self.LEFT_PARENTHESIS, tokens[i+1], self.OPERATOR_OR, tokens[i+4], self.RIGHT_PARENTHESIS]
             
        return tokens

    def evaluate_postfix(self, postfix):
        eval_stack = []
        for token in postfix:
            # print("current token: ", token)
            if token in self.LOGICAL_OPERATORS:
                if token == self.OPERATOR_AND:
                    # not sure if this is space inefficient cos it's creating a new list
                    # maybe figure out way to not create a new list
                    eval_stack.append(self.and_operation(eval_stack.pop(), eval_stack.pop()))
                elif token == self.OPERATOR_OR:
                    eval_stack.append(self.or_operation(eval_stack.pop(), eval_stack.pop()))
                elif token == self.OPERATOR_NOT:
                    eval_stack.append(self.not_operation(eval_stack.pop()))
            else:
                eval_stack.append(self.load_postings_list_from_term(token))
            # print("eval_stack: ", [len(x) for x in eval_stack], '\n')
        return eval_stack[0]

    def load_postings_list_from_term(self, term):
        if term not in self.dictionary:
            raise ValueError(f"'{term}' not found in dictionary")
        
        if term == LinkedList.EMPTY_SET_KEY:
            return LinkedList()
        
        offset, bytes_to_read, len_list = self.dictionary[term]

        # read the postings list from the postings file
        with open(self.postings_file, 'rb') as f:
            f.seek(offset)
            postings_list = pickle.loads(f.read(bytes_to_read))

        postings_ll = LinkedList()
        dummy = Node(None)
        postings_ll.head = dummy
        prev_node = dummy
        prev_skip_node = None
        skip_distance = -1 # keeps track of how far it is to node that is target of skip pointer

        for doc_id, skip_length in postings_list:
            new_node = Node(doc_id)
            prev_node.next = new_node
            prev_node = new_node
            
            # check if skip distance has reached 0
            skip_distance -= 1
            if skip_distance == 0:
                prev_skip_node.skip = new_node

            # if this node has a skip pointer, store it until the node to skip to is found
            if skip_length != 0:
                prev_skip_node = new_node
                skip_distance = skip_length

        postings_ll.head = dummy.next
        del dummy

        return postings_ll

    def and_operation(self, postings1, postings2):
        node1 = postings1.head
        node2 = postings2.head
        # to keep track of the previous intersecting node in postings1
        # because postings1 will be modified in place
        prev1 = None

        while node1 is not None and node2 is not None:
            if node1.data == node2.data:
                node1.skip = None # remove skip pointers
                node2 = node2.next
                prev1 = node1
                node1 = node1.next
            elif node1.data < node2.data:
                if node1.skip and node1.skip.data <= node2.data:
                    while node1.skip and node1.skip.data <= node2.data:
                        node1 = node1.skip
                # first intersection node should be made the new head
                if prev1 is None:
                    postings1.head = node1.next # remove node1 from postings1
                else:
                    prev1.next = node1.next # remove node1 from postings1
                node1 = node1.next
            else:
                if node2.skip and node2.skip.data <= node1.data:
                    while node2.skip and node2.skip.data <= node1.data:
                        node2 = node2.skip
                node2 = node2.next

        if prev1 is None:
            postings1.head = None # no intersections found
        else:
            prev1.next = None # disconnect remaining elements

        return postings1

    def or_operation(self, postings1, postings2):
        node1 = postings1.head
        node2 = postings2.head

        # dummy will be removed at the end
        dummy = Node(None)
        prev1 = dummy
        postings1.head = dummy

        while node1 is not None and node2 is not None:
            if node1.data < node2.data:
                node1.skip = None # remove skip pointer
                prev1.next = node1
                prev1 = node1
                node1 = node1.next
            elif node1.data > node2.data:
                node2.skip = None # remove skip pointer
                prev1.next = node2
                prev1 = node2
                node2 = node2.next
            else:
                # equal, add one and advance both
                node1.skip = None # remove skip pointer
                prev1.next = node1
                prev1 = node1
                node1 = node1.next
                node2 = node2.next
        
        # attach remainder of longer list
        if node1 is not None:
            prev1.next = node1
        else:
            prev1.next = node2

        postings1.head = dummy.next
        return postings1

    def not_operation(self, postings):
        universal_postings = self.load_postings_list_from_term(LinkedList.UNIVERSAL_SET_KEY)

        node1 = universal_postings.head
        node2 = postings.head

        if node2 is None:
            return universal_postings

        dummy = Node(None)
        dummy.next = node1
        prev1 = dummy
        universal_postings.head = dummy

        while node1 is not None and node2 is not None:
            if node1.data == node2.data:
                prev1.next = node1.next # prune out the current node1
                node1 = node1.next
                node2 = node2.next
            else:
                if node1.skip and node1.skip.data <= node2.data:
                    while node1.skip and node1.skip.data <= node2.data:
                        node1 = node1.skip
                prev1 = node1
                node1 = node1.next

        universal_postings.head = dummy.next
        return universal_postings
    
    # convert items between parentheses into sublists
    # e.g. ["a", "b", "(", "c", "(", "d", ")", ")"] -> ["a", "b", ["c", ["d"]]]
    def process_parentheses(self, lst):
        stack = [[]]  # stack to collect processed items
        for item in lst:
            if item == self.LEFT_PARENTHESIS:
                stack.append([])  # Start a new sublist when seeing '('
            elif item == self.RIGHT_PARENTHESIS:
                last_list = stack.pop()  # end current sublist
                if last_list: stack[-1].append(last_list)  # add ended sublist to the previous list
            else:
                stack[-1].append(item)  # add item to current sublist
        return stack  # Return the first item in the stack, which is the processed list
    
    # apply the recursive rearrange function to the query
    # then process the results back to list of tokens
    def rearrange_query(self, query):
        rearranged_str, _ = self.recursive_rearrange(query)

        # recreate the query from the processed string
        # mapping for special characters to operators
        operator_mapping = {'|': self.OPERATOR_OR, '&': self.OPERATOR_AND, '~': self.OPERATOR_NOT, '(': self.LEFT_PARENTHESIS, ')': self.RIGHT_PARENTHESIS}
        
        tokens = []
        token = ''
        for char in rearranged_str:
            if char in operator_mapping:
                if token == '-99' or token == '-100':
                    tokens.append(int(token))
                    token = ''
                elif token:
                    tokens.append(token)
                    token = ''
                tokens.append(operator_mapping[char])
            else:
                token += char

        return tokens

        
    # for a given list, split it by "OR" to obtain sublists that only contain "AND" and "NOT" operations
    # rearrange each sublist to process terms with the shortest postings list first
    # rearrange the order of the sublists by the shortest posting list in each sublist
    # if an encountered term is a list, recursively rearrange it
    # this function assumes the query is in a valid form, no out of place operators/terms
    def recursive_rearrange(self, query):
        # split list by "OR"
        or_lists = [list(group) for k, group in groupby(query, lambda x: x == self.OPERATOR_OR) if not k] # REFERENCE: https://stackoverflow.com/questions/14529523/python-split-for-lists
        max_length = self.dictionary[LinkedList.UNIVERSAL_SET_KEY][2]

        # iterate through each sublist that contains "AND" and "NOT" operations
        for i, or_list in enumerate(or_lists):

            # get lengths of postings list for each term
            for j, term in reversed(list(enumerate(or_list))):
                # remove "AND" and "NOT" from list
                if term == self.OPERATOR_NOT or term == self.OPERATOR_AND:
                    or_list.pop(j)
                elif type(term) == list:
                    if or_list[j-1] == self.OPERATOR_NOT:
                        term, (shortest_length, longest_length) = self.recursive_rearrange(term)
                        term = '~' + term
                        length = max_length - shortest_length # theoretical longest length of this term
                        or_list[j] = (term, length)
                    else:
                        term, (shortest_length, longest_length) = self.recursive_rearrange(term)
                        or_list[j] = (term, longest_length)
                else:
                    assert term in self.dictionary, f"term {term} not found in dictionary"
                    if or_list[j-1] == self.OPERATOR_NOT:
                        length = max_length - self.dictionary[term][2]
                        term = "~" + term
                    else:
                        length = self.dictionary[term][2]
                    or_list[j] = (term, length)

            # sort terms by length of postings list
            or_list.sort(key=lambda x: x[1]) 
            
            # store the new order of the terms and length of shortest postings list
            # shortest because the max of AND is the shorter of the 2 lists
            or_lists[i] = ('&'.join([str(x[0]) for x in or_list]), or_list[0][1]) 

        # sort sublists by length of shortest postings list
        or_lists.sort(key=lambda x: x[1])

        # return the new order of the sublists and range for lengths of this 'term'
        # shortest possible is just shortest length
        # longest is addition of all lengths
        return ('(' + '|'.join([x[0] for x in or_lists]) + ')', (or_lists[0][1], sum(x[1] for x in or_lists))) 


# a(33) AND b(55) OR c(22) AND d(44)
# ab(33) OR cd(22)
# abcd(33)
# NOT abcd(100-22?)

if __name__ == "__main__":

    #query = 'employee AND company AND NOT profit AND (analyst OR (yemen AND oman OR (test AND team)) OR american AND meet OR quota AND (loss OR assess AND joy)'
    #query = 'employee AND company AND PROFIT OR analyst AND american'
    #query = 'profit AND NOT profit OR NOT profit OR analyst'
    query = '(american OR analyst) AND NOT assess'
    qp = QueryProcessor('./dictionary', './postings')

    # print(qp.process_query(query))

    # manual processing to catch error
    try:
        tokens = list(qp.tokenize_query(query))

        print('tokens', tokens)

        # check for any invalid tokens and phrase queries
        invalid_tokens = []
        prev_token_is_term = False
        for t in tokens:
            if t in qp.dictionary:
                if prev_token_is_term:
                    print("phrase query detected, please ensure all terms all separated by operators||")
                    raise ValueError
                elif "&" in t or "|" in t or "~" in t:
                    invalid_tokens.append(t)
                prev_token_is_term = True
            else:
                prev_token_is_term = False
                if t not in qp.OPERATOR_LIST:
                    invalid_tokens.append(t)

        if len(invalid_tokens) > 0:
            print("invalid token(s): " + ", ".join(invalid_tokens))
            raise ValueError

        tokens = qp.optimise_query(tokens)

        postfix = qp.convert_to_postfix(tokens)

        result = qp.evaluate_postfix(postfix)
            
    except Exception as e:
        print("ERROR" + traceback.format_exc())
    
    print(result)
    #postfix = qp.convert_to_postfix(tokens)
    #print(postfix)
    # result = qp.evaluate_postfix(postfix)
    # print(result)

    # with open()
    # query_list = []
    # for query in query_list:
    #     result = qp.process_query(query)

    # print items in current directory
        # import os
        # print("Items in current directory:", os.listdir())

    # with open('dictionary', 'rb') as f:
    #     dictionary = pickle.load(f)
    # #dictionary = pickle.loads('dictionary')
    # print(dictionary)
    # print('b')

    # pl = qp.load_postings_list_from_term('of')
    # print(pl)
    
    # test if and_operation is working correctly
    # list1 = LinkedList()
    # list1.create_posting(list(range(0, 40, 1)))
    # list2 = LinkedList()
    # list2.create_posting(list(range(0, 40, 3)))
    # qp.and_operation(list2, list1)
    # print(list1)
                

