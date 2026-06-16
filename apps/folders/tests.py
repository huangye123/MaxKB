import json

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from folders.views import WorkspaceApplicationFolder


class WorkspaceApplicationFolderApiTest(SimpleTestCase):
    def test_application_folder_returns_default_folder(self):
        request = APIRequestFactory().get("/admin/api/workspace/default/APPLICATION/folder")
        response = WorkspaceApplicationFolder.as_view()(request, workspace_id="default")
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["message"], "Success")
        self.assertEqual(payload["data"], [
            {
                "id": "default",
                "name": "default",
                "desc": "",
                "parent_id": None,
                "type": "folder",
                "children": [],
            },
        ])

    def test_application_folder_ignores_expired_authorization_header(self):
        request = APIRequestFactory().get(
            "/admin/api/workspace/default/APPLICATION/folder",
            HTTP_AUTHORIZATION="Bearer expired-token",
        )
        response = WorkspaceApplicationFolder.as_view()(request, workspace_id="default")
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"][0]["id"], "default")
