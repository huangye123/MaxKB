import json

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from system_manage.views import DisplayInfo, SystemChatUser, SystemGroup, WorkspaceApplicationPage


class DisplayInfoApiTest(SimpleTestCase):
    def test_display_info_returns_default_ui_config(self):
        request = APIRequestFactory().get("/admin/api/display/info")
        response = DisplayInfo.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["message"], "Success")
        self.assertEqual(payload["data"]["title"], "MaxKB")
        self.assertEqual(payload["data"]["theme"], "#3370FF")

    def test_display_info_ignores_expired_authorization_header(self):
        request = APIRequestFactory().get(
            "/admin/api/display/info",
            HTTP_AUTHORIZATION="Bearer expired-token",
        )
        response = DisplayInfo.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["showUserManual"], True)


class WorkspaceApplicationPageApiTest(SimpleTestCase):
    def test_application_page_returns_empty_records(self):
        request = APIRequestFactory().get("/admin/api/workspace/default/application/1/30")
        response = WorkspaceApplicationPage.as_view()(request, workspace_id="default", current_page=1, page_size=30)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["message"], "Success")
        self.assertEqual(payload["data"], {"total": 0, "records": []})

    def test_application_page_ignores_expired_authorization_header(self):
        request = APIRequestFactory().get(
            "/admin/api/workspace/default/application/1/30",
            HTTP_AUTHORIZATION="Bearer expired-token",
        )
        response = WorkspaceApplicationPage.as_view()(request, workspace_id="default", current_page=1, page_size=30)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["records"], [])


class SystemGroupApiTest(SimpleTestCase):
    def test_system_group_returns_default_group(self):
        request = APIRequestFactory().get("/admin/api/system/group")
        response = SystemGroup.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["message"], "Success")
        self.assertEqual(payload["data"], [{"id": "default", "name": "\u9ed8\u8ba4\u7528\u6237\u7ec4"}])

    def test_system_group_ignores_expired_authorization_header(self):
        request = APIRequestFactory().get(
            "/admin/api/system/group",
            HTTP_AUTHORIZATION="Bearer expired-token",
        )
        response = SystemGroup.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"][0]["id"], "default")


class SystemChatUserApiTest(SimpleTestCase):
    def test_user_manage_page_returns_empty_page(self):
        request = APIRequestFactory().get("/admin/api/system/chat_user/user_manage/1/20")
        response = SystemChatUser.UserManagePage.as_view()(request, current_page=1, page_size=20)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["message"], "Success")
        self.assertEqual(payload["data"], {
            "total": 0,
            "records": [],
            "current": 1,
            "size": 20,
        })

    def test_user_manage_page_ignores_expired_authorization_header(self):
        request = APIRequestFactory().get(
            "/admin/api/system/chat_user/user_manage/1/20",
            HTTP_AUTHORIZATION="Bearer expired-token",
        )
        response = SystemChatUser.UserManagePage.as_view()(request, current_page=1, page_size=20)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["records"], [])
