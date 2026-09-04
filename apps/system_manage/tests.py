import json
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.urls import resolve
from rest_framework.test import APIRequestFactory

from common.auth import AnonymousAuthentication
from system_manage.views import (
    ChatUserAuthView,
    DisplayInfo,
    OperateLogView,
    SystemAuthView,
    SystemChatUser,
    SystemGroup,
    WorkspaceApplicationPage,
)
from system_manage.models import (
    ChatUser,
    ChatUserAuth,
    Log,
    PlatformSourceAuth,
    SettingType,
    SystemSetting,
    UserGroup,
    UserGroupRelation,
)
from users.models import User


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


class SystemGroupApiTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = User.objects.create(
            username="admin",
            nick_name="admin",
            email="admin@example.com",
            password="password",
            role="ADMIN",
        )

    def test_system_group_returns_user_groups_from_database(self):
        UserGroup.objects.create(id="default", name="默认用户组")
        UserGroup.objects.create(id="custom", name="自定义用户组")

        request = APIRequestFactory().get("/admin/api/system/group")
        with patch.object(SystemGroup, "authentication_classes", [AnonymousAuthentication]):
            response = SystemGroup.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["message"], "Success")
        self.assertEqual(payload["data"], [
            {"id": "custom", "name": "自定义用户组"},
            {"id": "default", "name": "默认用户组"},
        ])

    def test_system_group_requires_authentication(self):
        request = APIRequestFactory().get(
            "/admin/api/system/group",
        )
        response = SystemGroup.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(payload["code"], 1003)

    def test_system_group_user_list_returns_related_chat_users(self):
        group = UserGroup.objects.create(id="default", name="Default Group")
        chat_user = ChatUser.objects.create(
            username="alice",
            email="alice@example.com",
            password="encrypted",
            phone="",
            nick_name="Alice",
            source="LOCAL",
        )
        relation = UserGroupRelation.objects.create(user=chat_user, group=group)

        request = APIRequestFactory().get("/admin/api/system/group/default/user_list/1/20?username=ali")
        with patch.object(SystemGroup.UserListPage, "authentication_classes", [AnonymousAuthentication]):
            response = SystemGroup.UserListPage.as_view()(request, group_id="default", current_page=1, page_size=20)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["total"], 1)
        self.assertEqual(payload["data"]["records"][0]["id"], str(chat_user.id))
        self.assertEqual(payload["data"]["records"][0]["username"], "alice")
        self.assertEqual(payload["data"]["records"][0]["user_group_relation_id"], str(relation.id))


class SystemChatUserApiTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = User.objects.create(
            username="admin",
            nick_name="admin",
            email="admin@example.com",
            password="password",
            role="ADMIN",
        )
        self.default_group = UserGroup.objects.create(id="default", name="默认用户组")

    def _auth(self, request):
        return request

    def test_user_manage_page_returns_chat_users_with_groups(self):
        user = ChatUser.objects.create(
            username="1111",
            email="381538764@qq.com",
            password="encrypted",
            phone="",
            nick_name="2222",
            source="LOCAL",
        )
        UserGroupRelation.objects.create(user=user, group=self.default_group)

        request = self._auth(APIRequestFactory().get("/admin/api/system/chat_user/user_manage/1/20"))
        with patch.object(SystemChatUser.UserManagePage, "authentication_classes", [AnonymousAuthentication]):
            response = SystemChatUser.UserManagePage.as_view()(request, current_page=1, page_size=20)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["message"], "Success")
        self.assertEqual(payload["data"]["total"], 1)
        self.assertEqual(payload["data"]["current"], 1)
        self.assertEqual(payload["data"]["size"], 20)
        self.assertEqual(payload["data"]["records"][0]["username"], "1111")
        self.assertEqual(payload["data"]["records"][0]["user_group_ids"], ["default"])
        self.assertEqual(payload["data"]["records"][0]["user_group_names"], ["默认用户组"])

    def test_create_chat_user_saves_group_relations(self):
        request = self._auth(APIRequestFactory().post(
            "/admin/api/system/chat_user",
            {
                "username": "1111",
                "email": "381538764@qq.com",
                "password": "MaxKB@123..",
                "phone": "",
                "nick_name": "2222",
                "user_group_ids": ["default"],
            },
            format="json",
        ))
        with patch.object(SystemChatUser, "authentication_classes", [AnonymousAuthentication]):
            response = SystemChatUser.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["username"], "1111")
        self.assertEqual(payload["data"]["email"], "381538764@qq.com")
        self.assertEqual(payload["data"]["phone"], "")
        self.assertEqual(payload["data"]["is_active"], True)
        self.assertEqual(payload["data"]["nick_name"], "2222")
        self.assertEqual(payload["data"]["source"], "LOCAL")
        self.assertNotEqual(ChatUser.objects.get(username="1111").password, "MaxKB@123..")
        self.assertTrue(UserGroupRelation.objects.filter(user_id=payload["data"]["id"], group_id="default").exists())

    def test_chat_user_list_returns_all_chat_users_for_selector(self):
        ChatUser.objects.create(
            username="1111",
            email="381538764@qq.com",
            password="encrypted",
            phone="",
            nick_name="2222",
            source="LOCAL",
        )

        request = self._auth(APIRequestFactory().get("/admin/api/system/chat_user/list"))
        with patch.object(SystemChatUser.List, "authentication_classes", [AnonymousAuthentication]):
            response = SystemChatUser.List.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"][0]["username"], "1111")
        self.assertNotIn("password", payload["data"][0])

    def test_update_chat_user_replaces_groups_and_keeps_password_when_blank(self):
        user = ChatUser.objects.create(
            username="1111",
            email="old@example.com",
            password="existing-password",
            phone="",
            nick_name="old",
            source="LOCAL",
        )
        custom_group = UserGroup.objects.create(id="custom", name="自定义用户组")
        UserGroupRelation.objects.create(user=user, group=self.default_group)

        request = self._auth(APIRequestFactory().put(
            f"/admin/api/system/chat_user/{user.id}",
            {
                "id": str(user.id),
                "username": "1111",
                "email": "381538764@qq.com",
                "password": "",
                "phone": "123",
                "nick_name": "2222",
                "user_group_ids": ["custom"],
            },
            format="json",
        ))
        with patch.object(SystemChatUser.Operate, "authentication_classes", [AnonymousAuthentication]):
            response = SystemChatUser.Operate.as_view()(request, user_id=str(user.id))
        payload = json.loads(response.content)
        user.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["nick_name"], "2222")
        self.assertEqual(payload["data"]["phone"], "123")
        self.assertEqual(user.password, "existing-password")
        self.assertFalse(UserGroupRelation.objects.filter(user=user, group=self.default_group).exists())
        self.assertTrue(UserGroupRelation.objects.filter(user=user, group=custom_group).exists())

    def test_delete_chat_user_removes_user(self):
        user = ChatUser.objects.create(
            username="1111",
            email="381538764@qq.com",
            password="encrypted",
            phone="",
            nick_name="2222",
            source="LOCAL",
        )

        request = self._auth(APIRequestFactory().delete(f"/admin/api/system/chat_user/{user.id}"))
        with patch.object(SystemChatUser.Operate, "authentication_classes", [AnonymousAuthentication]):
            response = SystemChatUser.Operate.as_view()(request, user_id=str(user.id))
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload, {"code": 200, "message": "Success", "data": True})
        self.assertFalse(ChatUser.objects.filter(id=user.id).exists())

    def test_user_manage_page_requires_authentication(self):
        request = APIRequestFactory().get(
            "/admin/api/system/chat_user/user_manage/1/20",
        )
        response = SystemChatUser.UserManagePage.as_view()(request, current_page=1, page_size=20)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(payload["code"], 1003)


class ChatUserAuthApiTest(TestCase):
    def test_auth_detail_returns_empty_object_when_not_configured(self):
        request = APIRequestFactory().get("/admin/api/chat_user/auth/LDAP/detail")
        with patch.object(ChatUserAuthView.Operate, "authentication_classes", [AnonymousAuthentication]):
            response = ChatUserAuthView.Operate.as_view()(request, auth_type="LDAP")
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"], {})

    def test_update_ldap_auth_creates_record_and_returns_config(self):
        data = {
            "id": "",
            "auth_type": "LDAP",
            "config": {
                "ou": "1",
                "base_dn": "1",
                "password": "1",
                "ldap_filter": "1",
                "ldap_server": "1",
                "ldap_mapping": "1",
            },
            "type": "SSO",
            "is_active": True,
            "is_valid": True,
        }
        request = APIRequestFactory().put("/admin/api/chat_user/auth/LDAP/info", data, format="json")
        with patch.object(ChatUserAuthView.Operate, "authentication_classes", [AnonymousAuthentication]):
            response = ChatUserAuthView.Operate.as_view()(request, auth_type="LDAP")
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"], data["config"])
        self.assertTrue(ChatUserAuth.objects.filter(auth_type="LDAP", config=data["config"]).exists())

    def test_oidc_detail_keeps_config_fields_after_update(self):
        config = {
            "scope": "1",
            "state": "1",
            "clientId": "1",
            "redirectUrl": "http://172.16.2.101/chat/api/auth/oidc",
            "authEndpoint": "1",
            "clientSecret": "1",
            "fieldMapping": "{\"username\": \"preferred_username\", \"email\": \"email\"}",
            "tokenEndpoint": "1",
            "userInfoEndpoint": "1",
        }
        ChatUserAuth.objects.create(
            auth_type="OIDC",
            config=config,
            type="SSO",
            is_active=True,
            is_valid=True,
        )

        request = APIRequestFactory().get("/admin/api/chat_user/auth/OIDC/detail")
        with patch.object(ChatUserAuthView.Operate, "authentication_classes", [AnonymousAuthentication]):
            response = ChatUserAuthView.Operate.as_view()(request, auth_type="OIDC")
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["data"]["auth_type"], "OIDC")
        self.assertEqual(payload["data"]["config"], config)
        self.assertEqual(payload["data"]["type"], "SSO")
        self.assertTrue(payload["data"]["is_active"])
        self.assertTrue(payload["data"]["is_valid"])

    def test_platform_source_returns_empty_list_when_not_configured(self):
        request = APIRequestFactory().get("/admin/api/chat_user/auth/platform/source")
        with patch.object(ChatUserAuthView.PlatformSource, "authentication_classes", [AnonymousAuthentication]):
            response = ChatUserAuthView.PlatformSource.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"], [])

    def test_platform_source_save_and_validate(self):
        data = {
            "key": "wecom",
            "isActive": True,
            "isValid": False,
            "config": {
                "corp_id": "corp",
                "agent_id": "agent",
                "app_secret": "secret",
                "callback_url": "http://localhost/chat/api/auth/wecom",
            },
        }
        request = APIRequestFactory().post("/admin/api/chat_user/auth/platform/source", data, format="json")
        with patch.object(ChatUserAuthView.PlatformSource, "authentication_classes", [AnonymousAuthentication]):
            response = ChatUserAuthView.PlatformSource.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["auth_type"], "wecom")
        self.assertTrue(payload["data"]["is_active"])
        self.assertTrue(payload["data"]["is_valid"])

        request = APIRequestFactory().get("/admin/api/chat_user/auth/platform/source")
        with patch.object(ChatUserAuthView.PlatformSource, "authentication_classes", [AnonymousAuthentication]):
            response = ChatUserAuthView.PlatformSource.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(payload["data"][0]["auth_type"], "wecom")
        self.assertEqual(payload["data"][0]["config"], data["config"])
        self.assertFalse(hasattr(ChatUserAuth, "create_time"))
        self.assertEqual(ChatUserAuth._meta.db_table, "chat_user_platform_source")

        request = APIRequestFactory().put("/admin/api/chat_user/auth/platform/source", data, format="json")
        with patch.object(ChatUserAuthView.PlatformSource, "authentication_classes", [AnonymousAuthentication]):
            response = ChatUserAuthView.PlatformSource.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["data"], True)

    def test_ldap_connection_validation_returns_false_when_required_fields_missing(self):
        request = APIRequestFactory().post(
            "/admin/api/chat_user/auth/connection",
            {"auth_type": "LDAP", "config": {"ldap_server": "ldap://example.com"}},
            format="json",
        )
        with patch.object(ChatUserAuthView.Connection, "authentication_classes", [AnonymousAuthentication]):
            response = ChatUserAuthView.Connection.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["data"], False)

    def test_auth_detail_requires_authentication(self):
        request = APIRequestFactory().get("/admin/api/chat_user/auth/LDAP/detail")
        response = ChatUserAuthView.Operate.as_view()(request, auth_type="LDAP")
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(payload["code"], 1003)


class OperateLogApiTest(TestCase):
    def test_menu_operation_option_returns_frontend_options(self):
        request = APIRequestFactory().get("/admin/api/operate_log/menu_operation_option/")
        with patch.object(OperateLogView.MenuOperationOption, "authentication_classes", [AnonymousAuthentication]):
            response = OperateLogView.MenuOperationOption.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"][0], {
            "menu": "User management",
            "operate": "Log in",
            "menu_label": "用户管理",
            "operate_label": "登录",
        })
        self.assertIn({
            "menu": "Chat User/Authentication Configuration",
            "operate": "Add or modify Chat/Authentication Configuration",
            "menu_label": "对话用户/认证配置",
            "operate_label": "添加或修改对话/认证配置",
        }, payload["data"])

    def test_get_clean_time_defaults_to_180_and_save_updates_value(self):
        get_request = APIRequestFactory().get("/admin/api/operate_log/get_clean_time")
        with patch.object(OperateLogView.CleanTime, "authentication_classes", [AnonymousAuthentication]):
            response = OperateLogView.CleanTime.as_view()(get_request)
        payload = json.loads(response.content)

        self.assertEqual(payload["data"], 180)

        save_request = APIRequestFactory().post("/admin/api/operate_log/save", {"clean_time": 30}, format="json")
        with patch.object(OperateLogView.CleanTime, "authentication_classes", [AnonymousAuthentication]):
            response = OperateLogView.CleanTime.as_view()(save_request)
        payload = json.loads(response.content)

        self.assertEqual(payload["data"], 30)
        self.assertEqual(SystemSetting.objects.get(type=SettingType.LOG.value).meta["clean_time"], 30)

    def test_page_filters_logs_and_returns_frontend_record_shape(self):
        Log.objects.create(
            menu="Chat User/Authentication Configuration",
            operate="Add or modify Chat/Authentication Configuration",
            user={"username": "admin", "nick_name": "系统管理员"},
            status=200,
            ip_address="10.181.1.130",
            details={"path": "/admin/api/chat_user/auth/LDAP/info", "body": {}, "query": {}},
            operation_object={},
            workspace_id="None",
        )
        Log.objects.create(
            menu="User management",
            operate="Log in",
            user={"username": "guest"},
            status=500,
            ip_address="127.0.0.1",
            details={"path": "/admin/api/user/login", "body": {}, "query": {}},
            operation_object={"name": "guest"},
            workspace_id="default",
        )

        request = APIRequestFactory().get(
            "/admin/api/operate_log/1/20",
            {
                "menu": json.dumps(["Chat User/Authentication Configuration"]),
                "user": "adm",
                "status": "200",
                "ip_address": "10.181",
            },
        )
        with patch.object(OperateLogView.Page, "authentication_classes", [AnonymousAuthentication]):
            response = OperateLogView.Page.as_view()(request, current_page=1, page_size=20)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["total"], 1)
        self.assertEqual(payload["data"]["current"], 1)
        self.assertEqual(payload["data"]["size"], 20)
        record = payload["data"]["records"][0]
        self.assertEqual(record["menu"], "对话用户/认证配置")
        self.assertEqual(record["operate"], "添加或修改对话/认证配置")
        self.assertEqual(record["user"]["username"], "admin")
        self.assertEqual(record["workspace_id"], "None")
        self.assertEqual(record["workspace_name"], "")


class SystemAuthApiTest(TestCase):
    def test_platform_source_route_resolves(self):
        resolver_match = resolve("/admin/api/platform/source")

        self.assertEqual(resolver_match.func.view_class, SystemAuthView.PlatformSource)

    def test_platform_source_returns_empty_list_when_not_configured(self):
        request = APIRequestFactory().get("/admin/api/platform/source")
        with patch.object(SystemAuthView.PlatformSource, "authentication_classes", [AnonymousAuthentication]):
            response = SystemAuthView.PlatformSource.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"], [])

    def test_login_setting_returns_defaults_and_can_be_saved(self):
        request = APIRequestFactory().get("/admin/api/auth/setting")
        with patch.object(SystemAuthView.Setting, "authentication_classes", [AnonymousAuthentication]):
            response = SystemAuthView.Setting.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["default_value"], "LOCAL")
        self.assertEqual(payload["data"]["failed_attempts"], 5)
        self.assertEqual(payload["data"]["lock_time"], 10)
        self.assertEqual(payload["data"]["role_id"], "USER")
        self.assertEqual(payload["data"]["workspace_id"], "default")
        self.assertEqual(payload["data"]["permission"], "NOT_AUTH")
        self.assertEqual(payload["data"]["login_methods"], ["LOCAL", "LDAP", "CAS", "OIDC", "OAuth2", "SAML2"])
        self.assertIn({"label": "SAML2", "value": "SAML2"}, payload["data"]["auth_types"])

        data = {
            "default_value": "LDAP",
            "max_attempts": 2,
            "failed_attempts": 4,
            "lock_time": 15,
            "role_id": "USER",
            "workspace_id": "default",
            "permission": "VIEW",
            "login_methods": ["LOCAL", "LDAP"],
        }
        request = APIRequestFactory().put("/admin/api/auth/setting", data, format="json")
        with patch.object(SystemAuthView.Setting, "authentication_classes", [AnonymousAuthentication]):
            response = SystemAuthView.Setting.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload, {"code": 200, "message": "Success", "data": None})

        request = APIRequestFactory().get("/admin/api/auth/setting")
        with patch.object(SystemAuthView.Setting, "authentication_classes", [AnonymousAuthentication]):
            response = SystemAuthView.Setting.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["data"]["default_value"], "LDAP")
        self.assertEqual(payload["data"]["login_methods"], ["LOCAL", "LDAP"])
        self.assertEqual(payload["data"]["system_options"][0], {"label": "账号登录", "value": "LOCAL"})

    def test_auth_detail_and_update_use_platform_source_table(self):
        config = {
            "ou": "2",
            "base_dn": "2",
            "password": "2",
            "ldap_filter": "2",
            "ldap_server": "2",
            "ldap_mapping": "2",
        }
        data = {
            "id": "",
            "auth_type": "LDAP",
            "config": config,
            "type": "SSO",
            "is_active": True,
            "is_valid": True,
        }
        request = APIRequestFactory().put("/admin/api/auth/LDAP/info", data, format="json")
        with patch.object(SystemAuthView.Operate, "authentication_classes", [AnonymousAuthentication]):
            response = SystemAuthView.Operate.as_view()(request, auth_type="LDAP")
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["data"], config)
        self.assertEqual(PlatformSourceAuth._meta.db_table, "platform_source")
        self.assertTrue(PlatformSourceAuth.objects.filter(auth_type="LDAP", config=config).exists())

        request = APIRequestFactory().get("/admin/api/auth/LDAP/detail")
        with patch.object(SystemAuthView.Operate, "authentication_classes", [AnonymousAuthentication]):
            response = SystemAuthView.Operate.as_view()(request, auth_type="LDAP")
        payload = json.loads(response.content)

        self.assertEqual(payload["data"]["auth_type"], "LDAP")
        self.assertEqual(payload["data"]["config"], config)
        self.assertTrue(payload["data"]["is_active"])
        self.assertIn("create_time", payload["data"])
        self.assertIn("update_time", payload["data"])

    def test_saml2_auth_can_be_saved_and_returned(self):
        config = {
            "spAcs": "http://172.16.2.101/admin/api/saml2/sso",
            "mapping": "2",
            "idpMetaUrl": "2",
            "privateKey": "2",
            "spEntityId": "http://172.16.2.101/admin/api/saml2/metadata",
            "certificate": "2",
            "wantAssertionsSigned": True,
            "wantAuthnRequestsSigned": True,
        }
        data = {
            "id": "",
            "auth_type": "SAML2",
            "config": config,
            "type": "SSO",
            "is_active": True,
            "is_valid": True,
        }
        request = APIRequestFactory().put("/admin/api/auth/SAML2/info", data, format="json")
        with patch.object(SystemAuthView.Operate, "authentication_classes", [AnonymousAuthentication]):
            response = SystemAuthView.Operate.as_view()(request, auth_type="SAML2")
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["data"], config)

        request = APIRequestFactory().get("/admin/api/auth/SAML2/detail")
        with patch.object(SystemAuthView.Operate, "authentication_classes", [AnonymousAuthentication]):
            response = SystemAuthView.Operate.as_view()(request, auth_type="SAML2")
        payload = json.loads(response.content)

        self.assertEqual(payload["data"]["auth_type"], "SAML2")
        self.assertEqual(payload["data"]["config"], config)

    def test_connection_validates_required_fields(self):
        request = APIRequestFactory().post(
            "/admin/api/auth/connection",
            {"auth_type": "SAML2", "config": {"spAcs": "http://example.com/sso"}},
            format="json",
        )
        with patch.object(SystemAuthView.Connection, "authentication_classes", [AnonymousAuthentication]):
            response = SystemAuthView.Connection.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["data"], False)
