# Chat User Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为管理端聊天用户认证页面补齐后端认证配置查询、更新、扫码登录和连接校验接口。

**Architecture:** 在 `system_manage` 应用内新增 `ChatUserAuth` 持久化模型并映射实际表 `chat_user_platform_source`，视图层提供普通认证配置和扫码平台配置接口。普通认证按 `auth_type` 唯一保存，扫码平台复用同一表以平台 key 保存。

**Tech Stack:** Django 5.2、Django REST Framework、现有 `result.success` 响应封装、`TokenAuth` 鉴权、Django TestCase。

---

### Task 1: 接口测试

**Files:**
- Modify: `apps/system_manage/tests.py`

- [ ] **Step 1: Write failing tests**

新增 `ChatUserAuthApiTest`，验证未配置查询返回 `{}`、LDAP 更新响应返回 config、OIDC 查询保留字段、扫码平台初始为空数组、扫码保存后可查询、校验字段完整时返回 `true`、未鉴权返回 401。

- [ ] **Step 2: Run tests to verify failure**

Run: `.\.venv\Scripts\python.exe apps\manage.py test system_manage.tests.ChatUserAuthApiTest`

Expected: fail with import or attribute errors because `ChatUserAuthView` and model do not exist.

### Task 2: 模型与迁移

**Files:**
- Modify: `apps/system_manage/models/chat_user.py`
- Modify: `apps/system_manage/models/__init__.py`
- Create: `apps/system_manage/migrations/0006_chatuserauth.py`

- [ ] **Step 1: Add model**

Add `ChatUserAuth` with `id`, `auth_type`, `config`, `type`, `is_active`, and `is_valid`, mapped to `chat_user_platform_source`.

- [ ] **Step 2: Add migration**

Run: `.\.venv\Scripts\python.exe apps\manage.py makemigrations system_manage`

Expected: creates `0006_chatuserauth.py`.

### Task 3: 视图与路由

**Files:**
- Create: `apps/system_manage/views/chat_user_auth.py`
- Modify: `apps/system_manage/views/__init__.py`
- Modify: `apps/system_manage/urls.py`

- [ ] **Step 1: Implement serializers and helpers**

Create serializers for auth payload and platform payload. Add helpers to serialize records and validate required config fields.

- [ ] **Step 2: Implement views**

Add `ChatUserAuthView` with nested `Operate`, `Connection`, and `PlatformSource` APIViews.

- [ ] **Step 3: Register routes**

Add paths for `/chat_user/auth/<auth_type>/detail`, `/chat_user/auth/<auth_type>/info`, `/chat_user/auth/connection`, and `/chat_user/auth/platform/source`.

### Task 4: 验证

**Files:**
- No production changes unless tests reveal a defect.

- [ ] **Step 1: Run focused tests**

Run: `.\.venv\Scripts\python.exe apps\manage.py test system_manage.tests.ChatUserAuthApiTest`

Expected: all tests pass.

- [ ] **Step 2: Run system_manage tests**

Run: `.\.venv\Scripts\python.exe apps\manage.py test system_manage.tests`

Expected: all system_manage tests pass.

## Self-Review

范围覆盖：计划覆盖所有用户列出的接口，并补齐页面现有连接测试、扫码保存、扫码校验调用。  
占位检查：没有待定项。  
类型一致性：`auth_type/config/type/is_active/is_valid` 与前端请求和响应字段一致。
