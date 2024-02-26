import re
import pickle
from index import LinkedList, Node

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

    UNIVERSAL_SET_KEY = 0 # define this in index later, shouldn't be defined in this

    regex_pattern = r'\bAND\b|\bOR\b|\bNOT\b|[\(\)]|\w+'

    def __init__(self, dictionary_file, postings_file):
        self.dictionary_file = dictionary_file
        self.postings_file = postings_file
        #self.output_file = output_file
        
        with open(dictionary_file, 'rb') as f:
            self.dictionary = pickle.load(f)

        pass

    def process_query(self, query):
        try:
            tokens = list(self.tokenize_query(query))

            # check for any invalid tokens
            invalid_tokens = [token for token in tokens if token not in self.dictionary and token not in self.OPERATOR_LIST]
            if len(invalid_tokens) > 0:
                return "invalid token(s): " + ", ".join(invalid_tokens)

            postfix = self.convert_to_postfix(tokens)
            result = self.evaluate_postfix(postfix)
        except Exception as e:
            return "ERROR"
        
        return str(result)

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
                yield token.lower()
        
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
        universal_postings = self.load_postings_list_from_term(self.UNIVERSAL_SET_KEY)

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


if __name__ == "__main__":

    query = '(american OR analyst) AND NOT assess'
    qp = QueryProcessor('./dictionary', './postings')

    # print(qp.process_query(query))

    # manual processing to catch error
    tokens = qp.tokenize_query(query)
    postfix = qp.convert_to_postfix(tokens)
    print(postfix)
    result = qp.evaluate_postfix(postfix)
    print(result)

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
                

