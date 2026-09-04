# coding=utf-8
"""
    @project: MaxKB
    @Author：虎虎
    @file： system.py
    @date：2025/6/4 16:01
    @desc:
"""
import os

from django.db import models
from rest_framework import serializers
from django.core.cache import cache

from common.constants.cache_version import Cache_Version
from common.database_model_manage.database_model_manage import DatabaseModelManage
from common.utils.rsa_util import get_key_pair_by_sql
from maxkb import settings
from system_manage.models import SystemSetting


class SettingType(models.CharField):
    # Community Edition
    CE = "CE", "社区"
    # Enterprise Edition
    PE = "PE", "专业版"
    # Professional Edition
    EE = "EE", '企业版'


class SystemProfileResponseSerializer(serializers.Serializer):
    version = serializers.CharField(required=True, label="version")
    edition = serializers.CharField(required=True, label="edition")
    license_is_valid = serializers.BooleanField(required=True, label="License is valid")


class SystemProfileSerializer(serializers.Serializer):
    @staticmethod
    def profile():
        version = os.environ.get('MAXKB_VERSION')
        return {'version': version, 'edition': 'PE',
                'license_is_valid':  True,
                'rsa': get_key_pair_by_sql().get('key')}
