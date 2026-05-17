from types import SimpleNamespace
from unittest.mock import Mock, patch
import json

from django.test import RequestFactory
from django.test import SimpleTestCase
from django.test import override_settings
from rest_framework.request import Request

from common.exception.app_exception import AppAuthenticationFailed
from common.constants.permission_constants import Auth, RoleConstants
from users.serializers.user import UserManageSerializer, build_current_user_role_list
from users.serializers.login import LoginSerializer
from users.views.user import resolve_current_user_for_role_list, resolve_current_user_auth_for_debug
from system_manage.serializers.role import build_system_role_list, get_role_permission_tree, get_system_role_list
from system_manage.serializers.user_resource_permission import build_default_application_resource_permission
from system_manage.views.user_resource_permission import WorkSpaceUserResourcePermissionView
from users.views import LoginAuthSetting, Logout


class CurrentUserRoleListTest(SimpleTestCase):
    def test_builds_ordered_builtin_roles_from_role_models(self):
        roles = [
            SimpleNamespace(id="USER", name="\u666e\u901a\u7528\u6237", type="USER", internal=True),
            SimpleNamespace(id="ADMIN", name="\u7cfb\u7edf\u7ba1\u7406\u5458", type="ADMIN", internal=True),
            SimpleNamespace(id="WORKSPACE_MANAGE", name="\u5de5\u4f5c\u7a7a\u95f4\u7ba1\u7406\u5458", type="WORKSPACE_MANAGE", internal=True),
        ]

        result = build_current_user_role_list(roles)

        self.assertEqual([item["id"] for item in result], ["ADMIN", "WORKSPACE_MANAGE", "USER"])
        self.assertEqual(result[0]["name"], "\u7cfb\u7edf\u7ba1\u7406\u5458")
        self.assertEqual(result[1]["type"], "WORKSPACE_MANAGE")
        self.assertIs(result[2]["internal"], True)

    def test_falls_back_to_builtin_role_metadata(self):
        result = build_current_user_role_list(["WORKSPACE_MANAGE", "USER"])

        self.assertEqual(
            result,
            [
                {
                    "id": "WORKSPACE_MANAGE",
                    "name": "\u5de5\u4f5c\u7a7a\u95f4\u7ba1\u7406\u5458",
                    "type": "WORKSPACE_MANAGE",
                    "internal": True,
                },
                {"id": "USER", "name": "\u666e\u901a\u7528\u6237", "type": "USER", "internal": True},
            ],
        )

    def test_workspace_user_member_fallback_includes_admin_as_user(self):
        admin_user = SimpleNamespace(
            id="f0dd8f71-e4ee-11ee-8c84-a8a1595801ab",
            nick_name="\u7cfb\u7edf\u7ba1\u7406\u5458",
            email="",
        )
        serializer = Mock()
        serializer.get_user_members = UserManageSerializer.get_user_members

        with patch("users.serializers.user.DatabaseModelManage.get_model", return_value=None):
            with patch("users.serializers.user.QuerySet", return_value=SimpleNamespace(all=lambda: [admin_user])):
                result = UserManageSerializer().get_user_members("default")

        self.assertEqual(result, [
            {
                "id": "f0dd8f71-e4ee-11ee-8c84-a8a1595801ab",
                "nick_name": "\u7cfb\u7edf\u7ba1\u7406\u5458",
                "email": "",
                "roles": ["\u666e\u901a\u7528\u6237"],
            }
        ])


class CurrentUserRoleListAuthTest(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_uses_admin_user_in_debug_when_token_is_invalid(self):
        admin_user = SimpleNamespace(username="admin")
        request = RequestFactory().get(
            "/admin/api/role_list/current_user",
            HTTP_AUTHORIZATION="Bearer invalid-token",
        )
        auth = Mock()
        auth.authenticate.side_effect = AppAuthenticationFailed(1002, "invalid")
        users = Mock()
        users.objects.filter.return_value.first.return_value = admin_user

        resolved_user = resolve_current_user_for_role_list(request, auth, users)

        self.assertIs(resolved_user, admin_user)
        users.objects.filter.assert_called_once_with(username="admin")

    @override_settings(DEBUG=False)
    def test_invalid_token_fails_when_not_debug(self):
        request = RequestFactory().get(
            "/admin/api/role_list/current_user",
            HTTP_AUTHORIZATION="Bearer invalid-token",
        )
        auth = Mock()
        auth.authenticate.side_effect = AppAuthenticationFailed(1002, "invalid")

        with self.assertRaises(AppAuthenticationFailed):
            resolve_current_user_for_role_list(request, auth, Mock())

    @override_settings(DEBUG=True)
    def test_debug_user_manage_gets_admin_auth_when_token_is_invalid(self):
        admin_user = SimpleNamespace(username="admin")
        request = RequestFactory().get(
            "/admin/api/user_manage/1/20",
            HTTP_AUTHORIZATION="Bearer invalid-token",
        )
        auth = Mock()
        auth.authenticate.side_effect = AppAuthenticationFailed(1002, "invalid")
        users = Mock()
        users.objects.filter.return_value.first.return_value = admin_user

        resolved_user, resolved_auth = resolve_current_user_auth_for_debug(request, auth, users)

        self.assertIs(resolved_user, admin_user)
        self.assertIsInstance(resolved_auth, Auth)
        self.assertIn(RoleConstants.ADMIN.value.__str__(), resolved_auth.role_list)


class SystemRoleListTest(SimpleTestCase):
    def test_builds_internal_and_custom_roles_with_user_count(self):
        roles = [
            SimpleNamespace(
                id="USER",
                role_name="\u666e\u901a\u7528\u6237",
                internal=True,
                type="USER",
                create_user="f0dd8f71-e4ee-11ee-8c84-a8a1595801ab",
            ),
            SimpleNamespace(
                id="ADMIN",
                role_name="\u7cfb\u7edf\u7ba1\u7406\u5458",
                internal=True,
                type="ADMIN",
                create_user="f0dd8f71-e4ee-11ee-8c84-a8a1595801ab",
            ),
            SimpleNamespace(
                id="CUSTOM",
                role_name="Custom",
                internal=False,
                type="USER",
                create_user="f0dd8f71-e4ee-11ee-8c84-a8a1595801ab",
            ),
        ]

        result = build_system_role_list(roles, {"ADMIN": 1, "USER": 2})

        self.assertEqual([item["id"] for item in result["internal_role"]], ["ADMIN", "USER"])
        self.assertEqual(result["internal_role"][0]["user_count"], 1)
        self.assertEqual(result["internal_role"][1]["user_count"], 2)
        self.assertEqual(result["custom_role"][0]["id"], "CUSTOM")
        self.assertEqual(result["custom_role"][0]["user_count"], 0)

    def test_falls_back_to_builtin_roles_without_role_model(self):
        query_set = Mock()
        admin_user = SimpleNamespace(id="f0dd8f71-e4ee-11ee-8c84-a8a1595801ab")
        query_set.filter.return_value.first.return_value = admin_user
        query_set.values_list.return_value = ["ADMIN"]

        with patch("system_manage.serializers.role.DatabaseModelManage.get_model", return_value=None):
            with patch("system_manage.serializers.role.QuerySet", return_value=query_set):
                result = get_system_role_list()

        self.assertEqual([item["id"] for item in result["internal_role"]], ["ADMIN", "WORKSPACE_MANAGE", "USER"])
        self.assertEqual(result["internal_role"][0]["user_count"], 1)
        self.assertEqual(result["internal_role"][1]["user_count"], 0)
        self.assertEqual(result["custom_role"], [])

    def test_admin_permission_tree_enables_user_management(self):
        result = get_role_permission_tree("ADMIN")
        user_management = next(item for item in result if item["id"] == "USER_MANAGEMENT")
        permissions = user_management["children"][0]["permission"]

        self.assertEqual(user_management["children"][0]["id"], "USER_MANAGEMENT")
        self.assertIn("USER_MANAGEMENT:READ", [item["id"] for item in permissions])
        self.assertTrue(all(item["enable"] for item in permissions))


class UserResourcePermissionListTest(SimpleTestCase):
    def test_builds_default_application_root_permission(self):
        result = build_default_application_resource_permission("default", "f0dd8f71-e4ee-11ee-8c84-a8a1595801ab")

        self.assertEqual(result["id"], "default")
        self.assertEqual(result["name"], "\u6839\u76ee\u5f55")
        self.assertEqual(result["auth_target_type"], "APPLICATION")
        self.assertEqual(result["resource_type"], "folder")
        self.assertEqual(result["user_id"], "f0dd8f71-e4ee-11ee-8c84-a8a1595801ab")
        self.assertEqual(result["workspace_id"], "default")
        self.assertIsNone(result["icon"])
        self.assertIsNone(result["folder_id"])
        self.assertEqual(result["permission"], "MANAGE")

    @override_settings(DEBUG=True)
    def test_workspace_user_resource_permission_get_falls_back_in_debug(self):
        request = Request(RequestFactory().get(
            "/admin/api/workspace/default/user_resource_permission/user/f0dd8f71-e4ee-11ee-8c84-a8a1595801ab/resource/APPLICATION",
            HTTP_AUTHORIZATION="Bearer expired-token",
        ))
        admin_user = SimpleNamespace(id="f0dd8f71-e4ee-11ee-8c84-a8a1595801ab", username="admin")

        with patch("users.views.user.TokenAuth.authenticate", side_effect=AppAuthenticationFailed(1002, "Login expired")):
            with patch("users.views.user.User.objects.filter") as filter_mock:
                filter_mock.return_value.first.return_value = admin_user
                with patch("system_manage.views.user_resource_permission.UserResourcePermissionSerializer") as serializer:
                    serializer.return_value.list.return_value = [
                        build_default_application_resource_permission("default", str(admin_user.id))
                    ]
                    response = WorkSpaceUserResourcePermissionView().get(
                        request,
                        "default",
                        "f0dd8f71-e4ee-11ee-8c84-a8a1595801ab",
                        "APPLICATION",
                    )

        self.assertEqual(json.loads(response.content)["code"], 200)


class LogoutTest(SimpleTestCase):
    def test_logout_ignores_expired_authorization_header(self):
        request = RequestFactory().post(
            "/admin/api/user/logout",
            HTTP_AUTHORIZATION="Bearer expired-token",
        )

        with patch("users.views.login.cache.delete") as delete_mock:
            with patch("common.log.log.Log.save"):
                response = Logout.as_view()(request)

        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertIs(payload["data"], True)
        delete_mock.assert_called_once()


class LoginAuthSettingTest(SimpleTestCase):
    def test_login_auth_setting_returns_local_auth_config(self):
        request = RequestFactory().get("/admin/api/login/auth/setting")

        response = LoginAuthSetting.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"], {
            "default_value": "LOCAL",
            "max_attempts": 1,
            "login_methods": ["LOCAL"],
            "system_options": [
                {"label": "\u8d26\u53f7\u767b\u5f55", "value": "LOCAL"},
            ],
            "auth_types": [
                {"label": "\u8d26\u53f7\u767b\u5f55", "value": "LOCAL"},
            ],
        })

    def test_login_auth_setting_ignores_expired_authorization_header(self):
        request = RequestFactory().get(
            "/admin/api/login/auth/setting",
            HTTP_AUTHORIZATION="Bearer expired-token",
        )

        response = LoginAuthSetting.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["default_value"], "LOCAL")


class LoginEncryptedDataTest(SimpleTestCase):
    def test_login_uses_password_from_encrypted_json_payload(self):
        user = SimpleNamespace(
            id="f0dd8f71-e4ee-11ee-8c84-a8a1595801ab",
            username="admin",
            email="",
            password="stored-password",
            is_active=True,
        )

        with patch("users.serializers.login.decrypt", return_value='{"username":"admin","password":"MaxKB@123.."}'):
            with patch("users.serializers.login.LoginSerializer.get_auth_setting", return_value={}):
                with patch("users.serializers.login.DatabaseModelManage.get_model", return_value=None):
                    with patch("users.serializers.login.User.objects.filter") as filter_mock:
                        with patch("users.serializers.login.password_verify", return_value=True) as verify_mock:
                            with patch("users.serializers.login.needs_password_upgrade", return_value=False):
                                with patch("users.serializers.login.cache"):
                                    filter_mock.return_value.first.return_value = user

                                    result = LoginSerializer.login({
                                        "username": "admin",
                                        "encryptedData": "encrypted-json",
                                    })

        self.assertIn("token", result)
        verify_mock.assert_called_once_with("MaxKB@123..", "stored-password")

    def test_login_treats_non_json_encrypted_payload_as_password(self):
        user = SimpleNamespace(
            id="f0dd8f71-e4ee-11ee-8c84-a8a1595801ab",
            username="admin",
            email="",
            password="stored-password",
            is_active=True,
        )

        with patch("users.serializers.login.decrypt", return_value="MaxKB@123.."):
            with patch("users.serializers.login.LoginSerializer.get_auth_setting", return_value={}):
                with patch("users.serializers.login.DatabaseModelManage.get_model", return_value=None):
                    with patch("users.serializers.login.User.objects.filter") as filter_mock:
                        with patch("users.serializers.login.password_verify", return_value=True) as verify_mock:
                            with patch("users.serializers.login.needs_password_upgrade", return_value=False):
                                with patch("users.serializers.login.cache"):
                                    filter_mock.return_value.first.return_value = user

                                    result = LoginSerializer.login({
                                        "username": "admin",
                                        "encryptedData": "encrypted-password",
                                    })

        self.assertIn("token", result)
        verify_mock.assert_called_once_with("MaxKB@123..", "stored-password")
