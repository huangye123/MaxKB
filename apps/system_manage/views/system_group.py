from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import AnonymousAuthentication


class SystemGroup(APIView):
    authentication_classes = [AnonymousAuthentication]

    @extend_schema(
        methods=["GET"],
        description=_("Get system user group list"),
        operation_id=_("Get system user group list"),  # type: ignore
        tags=[_("System parameters")],  # type: ignore
    )
    def get(self, request: Request):
        return result.success([{"id": "default", "name": "默认用户组"}])
