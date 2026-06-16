# 聊天用户认证配置接口设计

## 目标

为管理端页面 `/admin/system/chat/authentication` 提供可持久化的认证配置接口，覆盖 LDAP、CAS、OIDC、OAuth2 和扫码登录配置。

## 接口范围

- `GET /admin/api/chat_user/auth/<auth_type>/detail` 查询单个认证配置。
- `PUT /admin/api/chat_user/auth/<auth_type>/info` 创建或更新单个认证配置，响应返回 `config`。
- `POST /admin/api/chat_user/auth/connection` 做 LDAP 配置字段完整性校验，返回布尔值。
- `GET /admin/api/chat_user/auth/platform/source` 查询扫码登录平台配置列表。
- `POST /admin/api/chat_user/auth/platform/source` 创建或更新扫码登录平台配置。
- `PUT /admin/api/chat_user/auth/platform/source` 校验扫码平台配置字段是否完整，返回布尔值。

## 数据模型

新增 `ChatUserAuth` 模型，映射实际表 `chat_user_platform_source`，保存 `id`、`auth_type`、`config`、`type`、`is_active` 和 `is_valid`。`auth_type` 唯一，普通 SSO 使用 `LDAP/CAS/OIDC/OAuth2`，扫码登录使用 `wecom/dingtalk/lark` 等平台 key。

## 行为

普通认证未配置时返回 `{}`。更新时以 URL 中的 `auth_type` 为准，保存请求体配置并返回 `config`。扫码登录未配置时返回空数组，保存后返回完整配置。所有接口沿用 `TokenAuth`，测试中通过 `AnonymousAuthentication` 覆盖鉴权。

## 测试

在 `apps/system_manage/tests.py` 增加接口级测试，覆盖未配置查询、更新后查询、OIDC 字段保持、扫码空列表、扫码保存与校验、LDAP 连接校验和鉴权要求。
