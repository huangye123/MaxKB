from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import AnonymousAuthentication


class WorkspaceApplicationPage(APIView):
    authentication_classes = [AnonymousAuthentication]

    @extend_schema(
        methods=["GET"],
        description=_("Get workspace application page compatibility response"),
        operation_id=_("Get workspace application page compatibility response"),  # type: ignore
        tags=[_("Application")],  # type: ignore
    )
    def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
        return result.success({
            "total": 0,
            "records": [],
        })
