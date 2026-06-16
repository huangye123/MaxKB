from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import AnonymousAuthentication


class DisplayInfo(APIView):
    authentication_classes = [AnonymousAuthentication]

    @extend_schema(
        methods=["GET"],
        description=_("Get display information"),
        operation_id=_("Get display information"),  # type: ignore
        tags=[_("System parameters")],  # type: ignore
    )
    def get(self, request: Request):
        return result.success({
            "theme": "#3370FF",
            "icon": "",
            "loginLogo": "",
            "loginImage": "",
            "title": "MaxKB",
            "slogan": "强大易用的企业级智能体平台",
            "showUserManual": True,
            "userManualUrl": "https://maxkb.cn/docs/v2/",
            "showForum": True,
            "forumUrl": "https://bbs.fit2cloud.com/c/mk/11",
            "showProject": True,
            "projectUrl": "https://github.com/1Panel-dev/MaxKB",
        })
