from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth.authenticate import TokenAuth
from common.db.search import page_search
from common.exception.app_exception import AppApiException
from common.utils.common import password_encrypt, query_params_to_single_dict
from system_manage.models import ChatUser, UserGroup, UserGroupRelation


class ChatUserPayload(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    nick_name = serializers.CharField(required=True, max_length=150)
    user_group_ids = serializers.ListField(
        child=serializers.CharField(max_length=128),
        required=False,
        allow_empty=True,
    )
    id = serializers.UUIDField(required=False)


class ChatUserQuery(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    nick_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    source = serializers.CharField(required=False, allow_blank=True)

    def get_queryset(self):
        self.is_valid(raise_exception=True)
        queryset = ChatUser.objects.all()
        username = self.validated_data.get("username")
        nick_name = self.validated_data.get("nick_name")
        email = self.validated_data.get("email")
        is_active = self.validated_data.get("is_active", None)
        source = self.validated_data.get("source")
        if username:
            queryset = queryset.filter(username__contains=username)
        if nick_name:
            queryset = queryset.filter(nick_name__contains=nick_name)
        if email:
            queryset = queryset.filter(email__contains=email)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        if source:
            queryset = queryset.filter(source=source)
        return queryset.order_by("-create_time")


def serialize_chat_user(chat_user: ChatUser, with_groups=False):
    data = {
        "id": str(chat_user.id),
        "username": chat_user.username,
        "email": chat_user.email,
        "phone": chat_user.phone,
        "is_active": chat_user.is_active,
        "nick_name": chat_user.nick_name,
        "create_time": chat_user.create_time,
        "update_time": chat_user.update_time,
        "source": chat_user.source,
    }
    if with_groups:
        relations = getattr(chat_user, "prefetched_group_relations", None)
        if relations is None:
            relations = UserGroupRelation.objects.filter(user=chat_user).select_related("group")
        data["user_group_ids"] = [relation.group_id for relation in relations]
        data["user_group_names"] = [relation.group.name for relation in relations]
    return data


def validate_groups(group_ids):
    if not group_ids:
        return []
    groups = list(UserGroup.objects.filter(id__in=group_ids))
    found_group_ids = {group.id for group in groups}
    missing_group_ids = [group_id for group_id in group_ids if group_id not in found_group_ids]
    if missing_group_ids:
        raise AppApiException(500, _("User group does not exist"))
    return groups


def ensure_unique_chat_user(data, chat_user_id=None):
    queryset = ChatUser.objects.filter(
        Q(username=data.get("username")) | Q(email=data.get("email")) | Q(nick_name=data.get("nick_name"))
    )
    if chat_user_id is not None:
        queryset = queryset.exclude(id=chat_user_id)
    existing = queryset.first()
    if existing is None:
        return
    if existing.username == data.get("username"):
        raise AppApiException(500, _("Username already exists"))
    if existing.email == data.get("email"):
        raise AppApiException(500, _("Email already exists"))
    if existing.nick_name == data.get("nick_name"):
        raise AppApiException(500, _("Nick name already exists"))


def replace_group_relations(chat_user, groups):
    UserGroupRelation.objects.filter(user=chat_user).delete()
    UserGroupRelation.objects.bulk_create(
        [UserGroupRelation(user=chat_user, group=group) for group in groups]
    )


class SystemChatUser(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(
        methods=["POST"],
        description=_("Create system chat user"),
        operation_id=_("Create system chat user"),  # type: ignore
        tags=[_("System parameters")],  # type: ignore
    )
    @transaction.atomic
    def post(self, request: Request):
        serializer = ChatUserPayload(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        password = data.get("password")
        if not password:
            raise AppApiException(500, _("Password is required"))
        ensure_unique_chat_user(data)
        groups = validate_groups(data.get("user_group_ids", []))
        chat_user = ChatUser.objects.create(
            username=data.get("username"),
            email=data.get("email"),
            password=password_encrypt(password),
            phone=data.get("phone") or "",
            nick_name=data.get("nick_name"),
            source="LOCAL",
            is_active=True,
        )
        replace_group_relations(chat_user, groups)
        return result.success(serialize_chat_user(chat_user))

    class List(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get system chat user list"),
            operation_id=_("Get system chat user list"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        def get(self, request: Request):
            queryset = ChatUserQuery(data=query_params_to_single_dict(request.query_params)).get_queryset()
            return result.success([serialize_chat_user(chat_user) for chat_user in queryset])

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["PUT"],
            description=_("Update system chat user"),
            operation_id=_("Update system chat user"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        @transaction.atomic
        def put(self, request: Request, user_id: str):
            chat_user = ChatUser.objects.filter(id=user_id).first()
            if chat_user is None:
                raise AppApiException(500, _("Chat user does not exist"))
            serializer = ChatUserPayload(data={**request.data, "id": user_id})
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            ensure_unique_chat_user(data, chat_user.id)
            groups = validate_groups(data.get("user_group_ids", []))

            chat_user.username = data.get("username")
            chat_user.email = data.get("email")
            chat_user.phone = data.get("phone") or ""
            chat_user.nick_name = data.get("nick_name")
            if data.get("password"):
                chat_user.password = password_encrypt(data.get("password"))
            chat_user.save()
            replace_group_relations(chat_user, groups)
            return result.success(serialize_chat_user(chat_user))

        @extend_schema(
            methods=["DELETE"],
            description=_("Delete system chat user"),
            operation_id=_("Delete system chat user"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        def delete(self, request: Request, user_id: str):
            chat_user = ChatUser.objects.filter(id=user_id).first()
            if chat_user is None:
                raise AppApiException(500, _("Chat user does not exist"))
            chat_user.delete()
            return result.success(True)

    class UserManagePage(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get system chat user page"),
            operation_id=_("Get system chat user page"),  # type: ignore
            tags=[_("System parameters")],  # type: ignore
        )
        def get(self, request: Request, current_page: int, page_size: int):
            queryset = (
                ChatUserQuery(data=query_params_to_single_dict(request.query_params))
                .get_queryset()
                .prefetch_related(
                    Prefetch(
                        "usergrouprelation_set",
                        queryset=UserGroupRelation.objects.select_related("group").order_by("group_id"),
                        to_attr="prefetched_group_relations",
                    )
                )
            )
            return result.success(
                page_search(current_page, page_size, queryset, lambda chat_user: serialize_chat_user(chat_user, True))
            )
