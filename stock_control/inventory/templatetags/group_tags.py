# inventory/templatetags/group_tags.py

from django import template

from inventory.utils import is_admin_user
from inventory.constants import LEGACY_ROLE_GROUPS, GROUP_NAME_TO_ROLE_KEY

register = template.Library()


@register.filter(name='has_role_or_admin')
def has_role_or_admin(user, group_name):
    if is_admin_user(user):
        return True
    group = group_name.strip()
    if user.groups.filter(name=group).exists():
        return True
    role_key = GROUP_NAME_TO_ROLE_KEY.get(group)
    if role_key:
        legacy_groups = [name for name, role in LEGACY_ROLE_GROUPS.items() if role == role_key]
        return user.groups.filter(name__in=legacy_groups).exists()
    return False


@register.filter(name='has_any_role')
def has_any_role(user, group_list):
    if is_admin_user(user):
        return True
    groups = [g.strip() for g in group_list.split(',') if g.strip()]
    if user.groups.filter(name__in=groups).exists():
        return True
    legacy_targets = []
    for group in groups:
        role_key = GROUP_NAME_TO_ROLE_KEY.get(group)
        if role_key:
            legacy_targets.extend([name for name, role in LEGACY_ROLE_GROUPS.items() if role == role_key])
    if legacy_targets:
        return user.groups.filter(name__in=legacy_targets).exists()
    return False


@register.filter(name='has_role')
def has_role(user, group_name):
    group = group_name.strip()
    if user.groups.filter(name=group).exists():
        return True
    role_key = GROUP_NAME_TO_ROLE_KEY.get(group)
    if role_key:
        legacy_groups = [name for name, role in LEGACY_ROLE_GROUPS.items() if role == role_key]
        return user.groups.filter(name__in=legacy_groups).exists()
    return False
