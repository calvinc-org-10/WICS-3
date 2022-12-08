from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()

@register.filter
@stringfilter
def eval_arith(expr):
    try:
        return eval(expr)
    except (SyntaxError, NameError, TypeError, ZeroDivisionError):
        return "-- INVALID --"
