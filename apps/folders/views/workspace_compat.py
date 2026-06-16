from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import AnonymousAuthentication


class WorkspaceApplicationFolder(APIView):
    authentication_classes = [AnonymousAuthentication]

    @extend_schema(
        methods=["GET"],
        description=_("Get workspace application folder compatibility response"),
        operation_id=_("Get workspace application folder compatibility response"),  # type: ignore
        tags=[_("Folder")],  # type: ignore
    )
    def get(self, request: Request, workspace_id: str):
        return result.success([
            {
                "id": "default",
                "name": "default",
                "desc": "",
                "parent_id": None,
                "type": "folder",
                "children": [],
            },
        ])
