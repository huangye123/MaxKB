from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from users.views.user import resolve_current_user_auth_for_debug
from system_manage.serializers.role import get_role_permission_tree, get_system_role_list


class SystemRole(APIView):
    @extend_schema(
        methods=["GET"],
        description=_("Get system role list"),
        operation_id=_("Get system role list"),  # type: ignore
        tags=[_("System parameters")],  # type: ignore
    )
    def get(self, request: Request):
        resolve_current_user_auth_for_debug(request)
        return result.success(get_system_role_list())


class SystemRolePermission(APIView):
    @extend_schema(
        methods=["GET"],
        description=_("Get system role permission"),
        operation_id=_("Get system role permission"),  # type: ignore
        tags=[_("System parameters")],  # type: ignore
    )
    def get(self, request: Request, role_id):
        resolve_current_user_auth_for_debug(request)
        return result.success(get_role_permission_tree(role_id))
