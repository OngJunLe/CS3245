import re


# should this be a class? like I instantiate a shunting yarder to do
# all the shunting?

class QueryProcessor:
    OPERATOR_OR = 1
    OPERATOR_AND = 2
    OPERATOR_NOT = 3
    OPERATOR_LIST = [OPERATOR_OR, OPERATOR_AND, OPERATOR_NOT]

    LEFT_PARENTHESIS = 0
    RIGHT_PARENTHESIS = -1

    regex_pattern = r'\bAND\b|\bOR\b|\bNOT\b|[\(\)]|\w+'

    def __init__(self):
        pass

    def process_query(self, query):
        tokens = self.tokenize_query(query)
        postfix = self.convert_to_postfix(tokens)
        return postfix
        #return self.evaluate_postfix(postfix)

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
                yield token
        
    def convert_to_postfix(self, tokens):
        output_queue = []
        operator_stack = []

        for token in tokens:
            # token = next(tokens)
            if token in self.OPERATOR_LIST:
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
        return
                
if __name__ == "__main__":
    
    #query = ['bill', 'OR', 'Gates', 'AND', '(', 'vista', 'OR', 'XP', ')', 'AND', 'NOT', 'mac']
    query = "bill OR Gates AND (vista OR XP) AND NOT mac"
    qp = QueryProcessor()
    print(qp.process_query(query))


                

