from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth.authenticate import TokenAuth
from common.db.search import page_search
from system_manage.models import UserGroup, UserGroupRelation


class SystemGroup(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(
        methods=["GET"],
        description=_("Get system user group list"),
        operation_id=_("Get system user group list"),  # type: ignore
        tags=[_("System parameters")],  # type: ignore
    )
    def get(self, request: Request):
        return result.success(list(UserGroup.objects.order_by("id").values("id", "name")))

    class UserListPage(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get system user group chat user page"),
            operation_id=_("Get system user group chat user page"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        def get(self, request: Request, group_id: str, current_page: int, page_size: int):
            username = request.query_params.get("username")
            queryset = UserGroupRelation.objects.filter(group_id=group_id).select_related("user").order_by(
                "-user__create_time"
            )
            if username:
                queryset = queryset.filter(user__username__contains=username)

            def serialize_relation(relation: UserGroupRelation):
                user = relation.user
                return {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "is_active": user.is_active,
                    "nick_name": user.nick_name,
                    "create_time": user.create_time,
                    "update_time": user.update_time,
                    "source": user.source,
                    "user_group_relation_id": str(relation.id),
                }

            return result.success(page_search(current_page, page_size, queryset, serialize_relation))
