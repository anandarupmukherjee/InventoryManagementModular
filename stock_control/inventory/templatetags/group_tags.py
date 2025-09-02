# inventory/templatetags/group_tags.py

from django import template

register = template.Library()

@register.filter(name='has_role_or_admin')
def has_role_or_admin(user, group_name):
    return getattr(user, 'is_admin', False) or user.groups.filter(name=group_name).exists()

@register.filter(name='has_any_role')
def has_any_role(user, group_list):
    if getattr(user, 'is_admin', False):
        return True
    groups = [g.strip() for g in group_list.split(',')]
    return user.groups.filter(name__in=groups).exists()
