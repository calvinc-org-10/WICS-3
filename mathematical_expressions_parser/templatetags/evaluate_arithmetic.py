from django import template
from django.template.defaultfilters import stringfilter
from mathematical_expressions_parser.eval import evaluate


register = template.Library()

@register.filter
@stringfilter
def eval_arith(expr):
    try:
        return evaluate(expr)
    except (SyntaxError, NameError, TypeError, ZeroDivisionError):
        return "-- INVALID --"
