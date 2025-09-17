ROLE_KEY_ADMIN = 'admin'
ROLE_KEY_STAFF = 'staff'
ROLE_KEY_USER = 'user'
ROLE_KEY_SUPPLIER = 'supplier'


ROLE_GROUP_MAP = {
    ROLE_KEY_ADMIN: 'Admin',
    ROLE_KEY_STAFF: 'Staff',
    ROLE_KEY_USER: 'User',
    ROLE_KEY_SUPPLIER: 'Supplier',
}


GROUP_NAME_TO_ROLE_KEY = {name: key for key, name in ROLE_GROUP_MAP.items()}


ROLE_LABELS = {
    ROLE_KEY_ADMIN: 'Admin',
    ROLE_KEY_STAFF: 'Staff',
    ROLE_KEY_USER: 'User',
    ROLE_KEY_SUPPLIER: 'Supplier',
}


ROLE_CHOICES = [(key, ROLE_LABELS[key]) for key in ROLE_LABELS]


ROLE_FEATURE_SUMMARY = {
    ROLE_KEY_ADMIN: [
        'Dashboard access',
        'User withdrawals',
        'Complete product overview',
        'Stock management tools',
        'Reporting & analytics',
        'User management',
    ],
    ROLE_KEY_STAFF: [
        'Dashboard access',
        'User withdrawals',
        'Product overview pages',
        'Stock management tools',
        'Purchase order management',
    ],
    ROLE_KEY_USER: [
        'Dashboard access',
        'User withdrawals',
        'Product overview pages',
    ],
    ROLE_KEY_SUPPLIER: [
        'Low stock lots',
        'Expired lots',
    ],
}


ALL_ROLE_KEYS = list(ROLE_LABELS.keys())


LEGACY_ROLE_GROUPS = {
    'Inventory Manager': ROLE_KEY_ADMIN,
    'Leica Staff': ROLE_KEY_USER,
}


ALL_MANAGED_GROUP_NAMES = set(ROLE_GROUP_MAP.values()) | set(LEGACY_ROLE_GROUPS.keys())
