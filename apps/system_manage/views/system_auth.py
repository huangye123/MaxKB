from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth.authenticate import TokenAuth
from system_manage.models import PlatformSourceAuth, SettingType, SystemSetting


__all__ = ["SystemAuthView"]

PLATFORM_AUTH_TYPES = {"wecom", "dingtalk", "lark"}

SYSTEM_AUTH_OPTIONS = [
    {"label": "账号登录", "value": "LOCAL"},
    {"label": "CAS", "value": "CAS"},
    {"label": "LDAP", "value": "LDAP"},
    {"label": "OAuth2", "value": "OAuth2"},
    {"label": "OIDC", "value": "OIDC"},
    {"label": "SAML2", "value": "SAML2"},
]

DEFAULT_LOGIN_SETTING = {
    "default_value": "LOCAL",
    "max_attempts": 1,
    "failed_attempts": 5,
    "lock_time": 10,
    "role_id": "USER",
    "workspace_id": "default",
    "permission": "NOT_AUTH",
    "login_methods": ["LOCAL", "LDAP", "CAS", "OIDC", "OAuth2", "SAML2"],
}

REQUIRED_CONFIG_FIELDS = {
    "LDAP": ["ldap_server", "base_dn", "password", "ou", "ldap_filter", "ldap_mapping"],
    "CAS": ["ldpUri", "validateUrl", "redirectUrl"],
    "OIDC": [
        "authEndpoint",
        "tokenEndpoint",
        "userInfoEndpoint",
        "scope",
        "clientId",
        "clientSecret",
        "fieldMapping",
        "redirectUrl",
    ],
    "OAuth2": [
        "authEndpoint",
        "tokenEndpoint",
        "userInfoEndpoint",
        "scope",
        "clientId",
        "clientSecret",
        "redirectUrl",
        "fieldMapping",
    ],
    "SAML2": [
        "spAcs",
        "mapping",
        "idpMetaUrl",
        "privateKey",
        "spEntityId",
        "certificate",
    ],
    "wecom": ["corp_id", "agent_id", "app_secret", "callback_url"],
    "dingtalk": ["corp_id", "app_key", "app_secret", "callback_url"],
    "lark": ["app_key", "app_secret", "callback_url"],
}


class LoginSettingPayload(serializers.Serializer):
    default_value = serializers.CharField(required=True, max_length=32)
    max_attempts = serializers.IntegerField(required=True)
    failed_attempts = serializers.IntegerField(required=True)
    lock_time = serializers.IntegerField(required=True)
    role_id = serializers.CharField(required=True, max_length=64)
    workspace_id = serializers.CharField(required=True, max_length=64)
    permission = serializers.CharField(required=True, max_length=64)
    login_methods = serializers.ListField(child=serializers.CharField(max_length=32), required=True)


class SystemAuthPayload(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    auth_type = serializers.CharField(required=False, allow_blank=True, max_length=32)
    config = serializers.JSONField(required=True)
    type = serializers.CharField(required=False, allow_blank=True, default="SSO", max_length=32)
    is_active = serializers.BooleanField(required=False, default=False)
    is_valid = serializers.BooleanField(required=False, default=True)


class PlatformSourcePayload(serializers.Serializer):
    key = serializers.CharField(required=False, allow_blank=True, max_length=32)
    auth_type = serializers.CharField(required=False, allow_blank=True, max_length=32)
    config = serializers.JSONField(required=True)
    isActive = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    isValid = serializers.BooleanField(required=False)
    is_valid = serializers.BooleanField(required=False)
    type = serializers.CharField(required=False, allow_blank=True, default="SCAN", max_length=32)


def get_login_setting_data():
    setting = SystemSetting.objects.filter(type=SettingType.LOGIN_AUTH.value).first()
    meta = setting.meta if setting is not None and isinstance(setting.meta, dict) else {}
    login_setting = meta.get("login_auth_setting", {})
    data = {**DEFAULT_LOGIN_SETTING, **login_setting}
    return {
        **data,
        "system_options": SYSTEM_AUTH_OPTIONS,
        "auth_types": SYSTEM_AUTH_OPTIONS,
    }


def save_login_setting(data):
    setting, _ = SystemSetting.objects.get_or_create(type=SettingType.LOGIN_AUTH.value, defaults={"meta": {}})
    meta = setting.meta if isinstance(setting.meta, dict) else {}
    setting.meta = {**meta, "login_auth_setting": data}
    setting.save()


def serialize_auth(auth: PlatformSourceAuth):
    return {
        "id": str(auth.id),
        "create_time": auth.create_time,
        "update_time": auth.update_time,
        "auth_type": auth.auth_type,
        "config": auth.config,
        "type": auth.type,
        "is_active": auth.is_active,
        "is_valid": auth.is_valid,
    }


def is_config_complete(auth_type, config):
    required_fields = REQUIRED_CONFIG_FIELDS.get(auth_type, [])
    return all(config.get(field) not in (None, "") for field in required_fields)


def get_platform_auth_type(data):
    return data.get("auth_type") or data.get("key")


def bool_from_alias(data, snake_key, camel_key, default=False):
    if snake_key in data:
        return data.get(snake_key)
    if camel_key in data:
        return data.get(camel_key)
    return default


class SystemAuthView(APIView):
    class Setting(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get system authentication setting"),
            operation_id=_("Get system authentication setting"),  # type: ignore
            tags=[_("System Authentication")],  # type: ignore
        )
        def get(self, request: Request):
            return result.success(get_login_setting_data())

        @extend_schema(
            methods=["PUT"],
            description=_("Update system authentication setting"),
            operation_id=_("Update system authentication setting"),  # type: ignore
            tags=[_("System Authentication")],  # type: ignore
        )
        @transaction.atomic
        def put(self, request: Request):
            serializer = LoginSettingPayload(data=request.data)
            serializer.is_valid(raise_exception=True)
            save_login_setting(serializer.validated_data)
            return result.success(None)

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get system authentication source"),
            operation_id=_("Get system authentication source"),  # type: ignore
            tags=[_("System Authentication")],  # type: ignore
        )
        def get(self, request: Request, auth_type: str):
            auth = PlatformSourceAuth.objects.filter(auth_type=auth_type).first()
            if auth is None:
                return result.success({})
            return result.success(serialize_auth(auth))

        @extend_schema(
            methods=["PUT"],
            description=_("Update system authentication source"),
            operation_id=_("Update system authentication source"),  # type: ignore
            tags=[_("System Authentication")],  # type: ignore
        )
        @transaction.atomic
        def put(self, request: Request, auth_type: str):
            serializer = SystemAuthPayload(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            config = data.get("config")
            auth, _ = PlatformSourceAuth.objects.update_or_create(
                auth_type=auth_type,
                defaults={
                    "config": config,
                    "type": data.get("type") or "SSO",
                    "is_active": data.get("is_active", False),
                    "is_valid": data.get("is_valid", True),
                },
            )
            return result.success(auth.config)

    class Connection(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["POST"],
            description=_("Validate system authentication connection"),
            operation_id=_("Validate system authentication connection"),  # type: ignore
            tags=[_("System Authentication")],  # type: ignore
        )
        def post(self, request: Request):
            serializer = SystemAuthPayload(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            auth_type = data.get("auth_type") or "LDAP"
            return result.success(is_config_complete(auth_type, data.get("config")))

    class PlatformSource(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get system authentication platform source"),
            operation_id=_("Get system authentication platform source"),  # type: ignore
            tags=[_("System Authentication")],  # type: ignore
        )
        def get(self, request: Request):
            queryset = PlatformSourceAuth.objects.filter(auth_type__in=PLATFORM_AUTH_TYPES).order_by("auth_type")
            return result.success([serialize_auth(auth) for auth in queryset])

        @extend_schema(
            methods=["POST"],
            description=_("Update system authentication platform source"),
            operation_id=_("Update system authentication platform source"),  # type: ignore
            tags=[_("System Authentication")],  # type: ignore
        )
        @transaction.atomic
        def post(self, request: Request):
            serializer = PlatformSourcePayload(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            auth_type = get_platform_auth_type(data)
            config = data.get("config")
            auth, _ = PlatformSourceAuth.objects.update_or_create(
                auth_type=auth_type,
                defaults={
                    "config": config,
                    "type": data.get("type") or "SCAN",
                    "is_active": bool_from_alias(data, "is_active", "isActive", False),
                    "is_valid": is_config_complete(auth_type, config),
                },
            )
            return result.success(serialize_auth(auth))

        @extend_schema(
            methods=["PUT"],
            description=_("Validate system authentication platform source"),
            operation_id=_("Validate system authentication platform source"),  # type: ignore
            tags=[_("System Authentication")],  # type: ignore
        )
        def put(self, request: Request):
            serializer = PlatformSourcePayload(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            auth_type = get_platform_auth_type(data)
            return result.success(is_config_complete(auth_type, data.get("config")))
