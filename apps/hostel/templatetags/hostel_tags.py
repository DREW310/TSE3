from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """
    Subtracts the argument from the value.
    Usage: {{ value|subtract:arg }}
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return ''

@register.filter
def filter_status(queryset, status):
    """
    Filter a queryset by status
    Usage: {{ queryset|filter_status:"pending" }}
    """
    return queryset.filter(status=status) 