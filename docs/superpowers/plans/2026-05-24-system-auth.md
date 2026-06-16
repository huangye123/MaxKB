# 系统登录认证接口适配实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 适配 `/admin/system/authentication` 页面需要的系统登录认证后端接口。

**Architecture:** 新增独立 `PlatformSourceAuth` 模型映射真实 `platform_source` 表，新增 `SystemAuthView` 处理 `/admin/api/auth/...` 接口，登录设置存入 `system_setting` 的独立配置项。保留已有对话用户认证接口，不复用 `chat_user_platform_source`。

**Tech Stack:** Django REST Framework、PostgreSQL JSONB、现有 `common.result` 响应包装。

---

### Task 1: 接口测试

**Files:**
- Modify: `apps/system_manage/tests.py`

- [ ] **Step 1: 添加系统认证接口测试**

覆盖登录设置默认值和保存、LDAP/CAS/OIDC/OAuth2/SAML2 查询保存、连接字段完整性、`platform_source` 表名映射。

- [ ] **Step 2: 运行测试确认失败**

运行 `python apps/manage.py test system_manage.tests.SystemAuthApiTest --keepdb`，预期因 `SystemAuthView` 或模型不存在失败。

### Task 2: 模型映射

**Files:**
- Modify: `apps/system_manage/models/chat_user.py`
- Create: `apps/system_manage/migrations/0008_platformsourceauth.py`

- [ ] **Step 1: 新增 `PlatformSourceAuth`**

字段匹配真实表：`create_time/update_time/id/auth_type/config/type/is_active/is_valid`，`db_table = "platform_source"`。

- [ ] **Step 2: 新增状态迁移**

迁移使用 `SeparateDatabaseAndState`，确保 ORM 状态存在，不破坏已存在表。

### Task 3: 视图与路由

**Files:**
- Create: `apps/system_manage/views/system_auth.py`
- Modify: `apps/system_manage/views/__init__.py`
- Modify: `apps/system_manage/urls.py`

- [ ] **Step 1: 实现 `SystemAuthView`**

提供 `Setting`、`Operate`、`Connection` 三类子视图。

- [ ] **Step 2: 挂载路由**

添加 `/auth/setting`、`/auth/connection`、`/auth/<auth_type>/detail`、`/auth/<auth_type>/info`。

### Task 4: 验证

**Files:**
- No code changes

- [ ] **Step 1: 运行语法检查**

运行 `python -m py_compile` 检查新增/修改 Python 文件。

- [ ] **Step 2: 运行迁移检查**

运行 `python apps/manage.py makemigrations system_manage --check --dry-run`。

- [ ] **Step 3: 运行接口脚本**

用 `APIRequestFactory` 直接调用登录设置、LDAP、SAML2 和连接测试接口，确认响应结构。
