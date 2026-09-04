from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth.authenticate import TokenAuth
from system_manage.models import ChatUserAuth


PLATFORM_AUTH_TYPES = {"wecom", "dingtalk", "lark"}

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
    "wecom": ["corp_id", "agent_id", "app_secret", "callback_url"],
    "dingtalk": ["corp_id", "app_key", "app_secret", "callback_url"],
    "lark": ["app_key", "app_secret", "callback_url"],
}


class ChatUserAuthPayload(serializers.Serializer):
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


def serialize_auth(auth: ChatUserAuth):
    return {
        "id": str(auth.id),
        "auth_type": auth.auth_type,
        "config": auth.config,
        "type": auth.type,
        "is_active": auth.is_active,
        "is_valid": auth.is_valid,
    }


def get_platform_auth_type(data):
    return data.get("auth_type") or data.get("key")


def bool_from_alias(data, snake_key, camel_key, default=False):
    if snake_key in data:
        return data.get(snake_key)
    if camel_key in data:
        return data.get(camel_key)
    return default


def is_config_complete(auth_type, config):
    required_fields = REQUIRED_CONFIG_FIELDS.get(auth_type, [])
    return all(bool(config.get(field)) for field in required_fields)


class ChatUserAuthView(APIView):
    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get chat user authentication configuration"),
            operation_id=_("Get chat user authentication configuration"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        def get(self, request: Request, auth_type: str):
            auth = ChatUserAuth.objects.filter(auth_type=auth_type).first()
            if auth is None:
                return result.success({})
            return result.success(serialize_auth(auth))

        @extend_schema(
            methods=["PUT"],
            description=_("Update chat user authentication configuration"),
            operation_id=_("Update chat user authentication configuration"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        @transaction.atomic
        def put(self, request: Request, auth_type: str):
            serializer = ChatUserAuthPayload(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            config = data.get("config")
            auth, _ = ChatUserAuth.objects.update_or_create(
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
            description=_("Validate chat user authentication connection"),
            operation_id=_("Validate chat user authentication connection"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        def post(self, request: Request):
            serializer = ChatUserAuthPayload(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            auth_type = data.get("auth_type") or "LDAP"
            return result.success(is_config_complete(auth_type, data.get("config")))

    class PlatformSource(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get chat user authentication platform source"),
            operation_id=_("Get chat user authentication platform source"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        def get(self, request: Request):
            queryset = ChatUserAuth.objects.filter(auth_type__in=PLATFORM_AUTH_TYPES).order_by("auth_type")
            return result.success([serialize_auth(auth) for auth in queryset])

        @extend_schema(
            methods=["POST"],
            description=_("Update chat user authentication platform source"),
            operation_id=_("Update chat user authentication platform source"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        @transaction.atomic
        def post(self, request: Request):
            serializer = PlatformSourcePayload(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            auth_type = get_platform_auth_type(data)
            config = data.get("config")
            auth, _ = ChatUserAuth.objects.update_or_create(
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
            description=_("Validate chat user authentication platform source"),
            operation_id=_("Validate chat user authentication platform source"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        def put(self, request: Request):
            serializer = PlatformSourcePayload(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            auth_type = get_platform_auth_type(data)
            return result.success(is_config_complete(auth_type, data.get("config")))
