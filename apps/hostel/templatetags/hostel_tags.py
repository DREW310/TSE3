from django import template
from django.utils import timezone

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

@register.filter
def active_assignments(room):
    """
    Get active assignments for a room that are currently valid
    Usage: {{ room|active_assignments }}
    """
    today = timezone.now().date()
    return room.assignments.filter(
        status='active',
        start_date__lte=today,
        end_date__gte=today
    )

@register.filter
def all_active_assignments(room):
    """
    Get all active assignments for a room regardless of date
    Usage: {{ room|all_active_assignments }}
    """
    return room.assignments.filter(status='active') 