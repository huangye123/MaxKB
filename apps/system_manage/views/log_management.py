import io
import json
from datetime import datetime, time, timedelta

import openpyxl
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth.authenticate import TokenAuth
from common.db.search import page_search
from common.exception.app_exception import AppApiException
from system_manage.models import Log, SettingType, SystemSetting


DEFAULT_CLEAN_TIME = 180
__all__ = ["OperateLogView"]

MENU_OPERATION_OPTIONS = [
    {
        "menu": "User management",
        "operate": "Log in",
        "menu_label": "用户管理",
        "operate_label": "登录",
    },
    {
        "menu": "User management",
        "operate": "Add user",
        "menu_label": "用户管理",
        "operate_label": "添加用户",
    },
    {
        "menu": "Chat user",
        "operate": "Update user information",
        "menu_label": "对话用户",
        "operate_label": "更新当前用户信息",
    },
    {
        "menu": "User management",
        "operate": "Delete user",
        "menu_label": "用户管理",
        "operate_label": "删除用户",
    },
    {
        "menu": "User group",
        "operate": "Create or update user group",
        "menu_label": "用户组",
        "operate_label": "创建或更新用户组",
    },
    {
        "menu": "Chat User/Authentication Configuration",
        "operate": "Test platform connection",
        "menu_label": "对话用户/认证配置",
        "operate_label": "测试平台连接",
    },
    {
        "menu": "User management",
        "operate": "Sign out",
        "menu_label": "用户管理",
        "operate_label": "登出",
    },
    {
        "menu": "Chat User/Authentication Configuration",
        "operate": "Add or modify Chat/Authentication Configuration",
        "menu_label": "对话用户/认证配置",
        "operate_label": "添加或修改对话/认证配置",
    },
    {
        "menu": "Chat User/Authentication Configuration",
        "operate": "Modify platform information",
        "menu_label": "对话用户/认证配置",
        "operate_label": "修改平台信息",
    },
    {
        "menu": "User management",
        "operate": "Modify current user password",
        "menu_label": "用户管理",
        "operate_label": "修改当前用户密码",
    },
    {
        "menu": "License",
        "operate": "Update license information",
        "menu_label": "License",
        "operate_label": "更新许可证信息",
    },
]

MENU_LABELS = {item["menu"]: item["menu_label"] for item in MENU_OPERATION_OPTIONS}
OPERATE_LABELS = {item["operate"]: item["operate_label"] for item in MENU_OPERATION_OPTIONS}


def expand_menu_values(menu_list):
    values = []
    for menu in menu_list:
        values.append(menu)
        label = MENU_LABELS.get(menu)
        if label is not None:
            values.append(label)
    return list(dict.fromkeys(values))


def parse_json_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else [parsed]
    except (TypeError, json.JSONDecodeError):
        return [value]


def parse_start_datetime(value):
    if not value:
        return None
    parsed_datetime = parse_datetime(value)
    if parsed_datetime is not None:
        return timezone.make_aware(parsed_datetime) if timezone.is_naive(parsed_datetime) else parsed_datetime
    parsed_date = parse_date(value)
    if parsed_date is None:
        return None
    return timezone.make_aware(datetime.combine(parsed_date, time.min))


def parse_end_datetime(value):
    if not value:
        return None
    parsed_datetime = parse_datetime(value)
    if parsed_datetime is not None:
        return timezone.make_aware(parsed_datetime) if timezone.is_naive(parsed_datetime) else parsed_datetime
    parsed_date = parse_date(value)
    if parsed_date is None:
        return None
    return timezone.make_aware(datetime.combine(parsed_date + timedelta(days=1), time.min))


def get_clean_time_value():
    setting = SystemSetting.objects.filter(type=SettingType.LOG.value).first()
    if setting is None or not isinstance(setting.meta, dict):
        return DEFAULT_CLEAN_TIME
    return setting.meta.get("clean_time", DEFAULT_CLEAN_TIME)


def serialize_log(log: Log):
    return {
        "id": str(log.id),
        "menu": MENU_LABELS.get(log.menu, log.menu),
        "operate": OPERATE_LABELS.get(log.operate, log.operate),
        "user": log.user or {},
        "status": log.status,
        "ip_address": log.ip_address,
        "details": log.details or {},
        "create_time": log.create_time,
        "update_time": log.update_time,
        "operation_object": log.operation_object or {},
        "workspace_id": log.workspace_id,
        "workspace_name": "" if log.workspace_id in ("None", "default", None) else log.workspace_id,
    }


def build_operate_log_queryset(query_params):
    queryset = Log.objects.all()

    start_time = parse_start_datetime(query_params.get("start_time"))
    if start_time is not None:
        queryset = queryset.filter(create_time__gte=start_time)

    end_time = parse_end_datetime(query_params.get("end_time"))
    if end_time is not None:
        queryset = queryset.filter(create_time__lt=end_time)

    menu_list = parse_json_list(query_params.get("menu"))
    if menu_list:
        queryset = queryset.filter(menu__in=expand_menu_values(menu_list))

    workspace_ids = parse_json_list(query_params.get("workspace_ids"))
    if workspace_ids:
        queryset = queryset.filter(workspace_id__in=workspace_ids)

    status = query_params.get("status")
    if status not in (None, ""):
        queryset = queryset.filter(status=int(status))

    user = query_params.get("user")
    if user:
        queryset = queryset.filter(user__username__icontains=user)

    ip_address = query_params.get("ip_address")
    if ip_address:
        queryset = queryset.filter(ip_address__icontains=ip_address)

    return queryset.order_by("-create_time")


def export_logs(queryset):
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "operate_log"
    headers = ["菜单", "操作", "用户", "状态", "IP", "操作时间", "详情"]
    worksheet.append(headers)
    for log in queryset:
        record = serialize_log(log)
        worksheet.append([
            record["menu"],
            record["operate"],
            record["user"].get("username", ""),
            record["status"],
            record["ip_address"],
            record["create_time"].strftime("%Y-%m-%d %H:%M:%S") if record["create_time"] else "",
            json.dumps(record["details"], ensure_ascii=False),
        ])
    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)
    response = HttpResponse(
        stream.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="log.xlsx"'
    return response


class OperateLogView(APIView):
    class MenuOperationOption(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get operate log menu operation options"),
            operation_id=_("Get operate log menu operation options"),  # type: ignore
            tags=[_("Operation Log")],  # type: ignore
        )
        def get(self, request: Request):
            return result.success(MENU_OPERATION_OPTIONS)

    class CleanTime(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get operate log clean time"),
            operation_id=_("Get operate log clean time"),  # type: ignore
            tags=[_("Operation Log")],  # type: ignore
        )
        def get(self, request: Request):
            return result.success(get_clean_time_value())

        @extend_schema(
            methods=["POST"],
            description=_("Save operate log clean time"),
            operation_id=_("Save operate log clean time"),  # type: ignore
            tags=[_("Operation Log")],  # type: ignore
        )
        def post(self, request: Request):
            clean_time = request.data.get("clean_time") if isinstance(request.data, dict) else request.data
            try:
                clean_time = int(clean_time)
            except (TypeError, ValueError):
                raise AppApiException(500, _("Clean time must be an integer"))
            if clean_time < 1:
                raise AppApiException(500, _("Clean time must be greater than 0"))
            SystemSetting.objects.update_or_create(
                type=SettingType.LOG.value,
                defaults={"meta": {"clean_time": clean_time}},
            )
            return result.success(clean_time)

    class Page(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["GET"],
            description=_("Get operate log page"),
            operation_id=_("Get operate log page"),  # type: ignore
            tags=[_("Operation Log")],  # type: ignore
        )
        def get(self, request: Request, current_page: int, page_size: int):
            queryset = build_operate_log_queryset(request.query_params)
            return result.success(page_search(current_page, page_size, queryset, serialize_log))

    class Export(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=["POST"],
            description=_("Export operate log"),
            operation_id=_("Export operate log"),  # type: ignore
            tags=[_("Operation Log")],  # type: ignore
        )
        def post(self, request: Request):
            queryset = build_operate_log_queryset(request.query_params)
            return export_logs(queryset)
