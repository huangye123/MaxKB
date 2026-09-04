from collections import Counter
from collections import OrderedDict

from django.db.models import QuerySet

from common.constants.permission_constants import Group, PermissionConstants, Permission_Label, RoleConstants, \
    SystemGroup, get_default_permission_list_by_role
from common.database_model_manage.database_model_manage import DatabaseModelManage
from users.models import User

ROLE_ORDER = {
    RoleConstants.ADMIN.value.name: 0,
    RoleConstants.WORKSPACE_MANAGE.value.name: 1,
    RoleConstants.USER.value.name: 2,
}


def _role_attr(role, name, default=None):
    value = getattr(role, name, default)
    return default if value is None else value


def _serialize_role(role, user_count):
    role_id = str(_role_attr(role, "id", ""))
    return {
        "id": role_id,
        "role_name": _role_attr(role, "role_name", _role_attr(role, "name", role_id)),
        "internal": bool(_role_attr(role, "internal", True)),
        "type": str(_role_attr(role, "type", role_id)),
        "create_user": str(_role_attr(role, "create_user", "")),
        "user_count": user_count.get(role_id, 0),
    }


def build_system_role_list(roles, user_count):
    internal_role = []
    custom_role = []
    for role in roles:
        role_item = _serialize_role(role, user_count)
        if role_item["internal"]:
            internal_role.append(role_item)
        else:
            custom_role.append(role_item)
    internal_role.sort(key=lambda item: (ROLE_ORDER.get(item["id"], 100), item["id"]))
    custom_role.sort(key=lambda item: item["role_name"])
    return {
        "internal_role": internal_role,
        "custom_role": custom_role,
    }


def get_system_role_list():
    role_model = DatabaseModelManage.get_model("role_model")
    workspace_user_role_mapping_model = DatabaseModelManage.get_model("workspace_user_role_mapping")
    if role_model is None:
        admin_user = QuerySet(User).filter(username="admin").first()
        user_count = Counter(QuerySet(User).values_list("role", flat=True))
        return build_system_role_list(
            [
                type("RoleItem", (), {
                    "id": role.value.name,
                    "role_name": _default_role_name(role.value.name),
                    "internal": True,
                    "type": role.value.name,
                    "create_user": getattr(admin_user, "id", ""),
                })
                for role in [RoleConstants.ADMIN, RoleConstants.WORKSPACE_MANAGE, RoleConstants.USER]
            ],
            user_count,
        )

    user_count = {}
    if workspace_user_role_mapping_model is not None:
        role_ids_by_user = QuerySet(workspace_user_role_mapping_model).values_list("role_id", "user_id").distinct()
        user_count = Counter(role_id for role_id, _ in role_ids_by_user)

    return build_system_role_list(QuerySet(role_model).all(), user_count)


def _default_role_name(role_id):
    return {
        RoleConstants.ADMIN.value.name: "\u7cfb\u7edf\u7ba1\u7406\u5458",
        RoleConstants.WORKSPACE_MANAGE.value.name: "\u5de5\u4f5c\u7a7a\u95f4\u7ba1\u7406\u5458",
        RoleConstants.USER.value.name: "\u666e\u901a\u7528\u6237",
    }.get(role_id, role_id)


def get_role_permission_tree(role_id):
    role = RoleConstants.__members__.get(role_id)
    if role is None:
        enabled_permissions = set()
    else:
        enabled_permissions = {str(permission.value) for permission in get_default_permission_list_by_role(role)}
    return build_role_permission_tree(enabled_permissions)


def build_role_permission_tree(enabled_permissions):
    group_map = OrderedDict()
    for permission_constant in PermissionConstants:
        permission = permission_constant.value
        if not permission.is_ee or not permission.parent_group:
            continue
        for parent_group in permission.parent_group:
            if not isinstance(parent_group, SystemGroup):
                continue
            parent_id = parent_group.value
            child_id = permission.group.value
            parent = group_map.setdefault(parent_id, {
                "id": parent_id,
                "name": str(Permission_Label.get(parent_id, parent_id)),
                "children": OrderedDict(),
            })
            child = parent["children"].setdefault(child_id, {
                "id": child_id,
                "name": str(Permission_Label.get(child_id, child_id)),
                "permission": [],
                "enable": False,
            })
            permission_id = str(permission)
            enabled = permission_id in enabled_permissions
            child["permission"].append({
                "id": permission_id,
                "name": str(Permission_Label.get(permission.operate.value, permission.operate.value)),
                "enable": enabled,
            })
            child["enable"] = child["enable"] or enabled

    return [
        {
            "id": parent["id"],
            "name": parent["name"],
            "children": list(parent["children"].values()),
        }
        for parent in group_map.values()
    ]
