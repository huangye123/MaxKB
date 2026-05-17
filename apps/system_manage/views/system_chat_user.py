from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import AnonymousAuthentication
from common.result import Page


class SystemChatUser(APIView):
    class UserManagePage(APIView):
        authentication_classes = [AnonymousAuthentication]

        @extend_schema(
            methods=["GET"],
            description=_("Get system chat user page"),
            operation_id=_("Get system chat user page"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        def get(self, request: Request, current_page: int, page_size: int):
            return result.success(Page(0, [], current_page, page_size))
