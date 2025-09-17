from typing import Optional

from django.contrib.auth.models import Group, User

from .constants import (
    ROLE_GROUP_MAP,
    ROLE_KEY_ADMIN,
    ROLE_KEY_STAFF,
    ROLE_KEY_SUPPLIER,
    ROLE_KEY_USER,
    LEGACY_ROLE_GROUPS,
    ALL_MANAGED_GROUP_NAMES,
)


def ensure_role_groups() -> None:
    """Ensure the baseline role groups exist in the database."""
    for group_name in ROLE_GROUP_MAP.values():
        Group.objects.get_or_create(name=group_name)


def _get_group_for_role(role_key: str) -> Optional[Group]:
    group_name = ROLE_GROUP_MAP.get(role_key)
    if not group_name:
        return None
    ensure_role_groups()
    return Group.objects.filter(name=group_name).first()


def set_user_role(user: User, role_key: str) -> None:
    """Assign the user to the requested role group and update admin flag."""
    if role_key not in ROLE_GROUP_MAP:
        return

    ensure_role_groups()

    # Remove from all managed role groups first
    user.groups.remove(*user.groups.filter(name__in=ALL_MANAGED_GROUP_NAMES))

    role_group = _get_group_for_role(role_key)
    if role_group:
        user.groups.add(role_group)

    user.is_staff = role_key == ROLE_KEY_ADMIN
    user.save(update_fields=['is_staff'])


def get_user_role(user: User) -> Optional[str]:
    """Return the canonical role key for the user."""
    if not isinstance(user, User):
        return None

    ensure_role_groups()

    if user.groups.filter(name=ROLE_GROUP_MAP[ROLE_KEY_ADMIN]).exists():
        return ROLE_KEY_ADMIN
    for role_key in (ROLE_KEY_STAFF, ROLE_KEY_USER, ROLE_KEY_SUPPLIER):
        group_name = ROLE_GROUP_MAP[role_key]
        if user.groups.filter(name=group_name).exists():
            return role_key

    # Legacy groups support
    for legacy_group, mapped_role in LEGACY_ROLE_GROUPS.items():
        if user.groups.filter(name=legacy_group).exists():
            return mapped_role

    if user.is_staff:
        return ROLE_KEY_ADMIN
    return None


def is_admin_user(user: User) -> bool:
    if not isinstance(user, User):
        return False
    if user.is_superuser:
        return True
    return get_user_role(user) == ROLE_KEY_ADMIN
