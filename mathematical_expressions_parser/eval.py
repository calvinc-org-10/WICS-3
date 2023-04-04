"""
Taken from https://github.com/blakeohare/Mathematical-Expressions-Parser
"""
# import math
from mathematical_expressions_parser.math_parser import MathParser

def evaluate(expression, in_vars = None):
    """
    I'll do a docstring one day
    """
    try:
        pars = MathParser(expression, in_vars)
        value = pars.getValue()
    except Exception as ex:
        raise ex
        # value = 0

    # Return an integer type if the answer is an integer
    if int(value) == value:
        return int(value)

    # If Python made some silly precision error like x.99999999999996, just return x+1 as an integer
    epsilon = 0.0000000001
    if int(value + epsilon) != int(value):
        return int(value + epsilon)
    if int(value - epsilon) != int(value):
        return int(value)
    return value

if __name__ == "__main__":
    testexpressions = [
        #{'exp_to_eval':"cos(x+4*3) + 2 * 3", 'vars':{ 'x': 5  }},
        #{'exp_to_eval':"exp(0)", 'vars':None},
        #{'exp_to_eval':"-(1 + 2) * 3", 'vars':None},
        #{'exp_to_eval':"(1-2)/3.0 + 0.0000", 'vars':None},
        #{'exp_to_eval':"abs(-2) + pi / 4", 'vars':None},
        #{'exp_to_eval':"(x + e * 10) / 10", 'vars':{ 'x' : 3 }},
        #{'exp_to_eval':"1.0 / 3 * 6", 'vars':None},
        #{'exp_to_eval':"(1 - 1 + -1) * pi", 'vars':None},
        #{'exp_to_eval':"cos(pi) * 1", 'vars':None},
        #{'exp_to_eval':"atan2(2, 1)", 'vars':None},
        #{'exp_to_eval':"hypot(5, 12)", 'vars':None},
        #{'exp_to_eval':"pow(3, 5)", 'vars':None},
        #{'exp_to_eval':"800*101+84+790+800*2+766+796+780", 'vars': None},   # 85616
        #{'exp_to_eval':"25+48*(2*35+1)", 'vars': None},   # 3433
        {'exp_to_eval':"40+6+2600*11+*589+457+3+1467+2*100+20+1720+893+5", 'vars':None},
    ]
    for TestE in testexpressions:
        print(TestE['exp_to_eval']," = ", evaluate(TestE['exp_to_eval'], TestE['vars'] ) )
