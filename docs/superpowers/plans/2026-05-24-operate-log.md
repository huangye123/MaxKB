# 操作日志接口适配实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 适配 `/admin/operate` 页面需要的操作日志菜单、清理时间、分页查询、保存和导出接口。

**Architecture:** 在 `system_manage` 后端新增 `OperateLogView`，直接读取现有 `log` 表和 `system_setting` 表。菜单选项使用固定枚举，分页查询按前端参数过滤并序列化为页面示例结构。

**Tech Stack:** Django REST Framework、现有 `common.result` 响应包装、`Log` 和 `SystemSetting` 模型。

---

### Task 1: 接口契约测试

**Files:**
- Modify: `apps/system_manage/tests.py`

- [ ] **Step 1: 添加失败测试**

在 `apps/system_manage/tests.py` 中导入 `OperateLogView`、`Log`、`SystemSetting`、`SettingType`，新增 `OperateLogApiTest`，覆盖菜单选项、清理时间默认值/保存值、分页查询过滤和字段结构。

- [ ] **Step 2: 运行测试确认失败**

运行 `python apps/manage.py test system_manage.tests.OperateLogApiTest --keepdb`，预期因为 `OperateLogView` 尚未实现或未导入而失败。

### Task 2: 视图实现

**Files:**
- Modify: `apps/system_manage/views/log_management.py`

- [ ] **Step 1: 实现固定菜单枚举**

定义 `MENU_OPERATION_OPTIONS`，字段与用户提供示例一致。

- [ ] **Step 2: 实现查询过滤**

支持 `start_time`、`end_time`、`menu`、`workspace_ids`、`status`、`user`、`ip_address` 查询参数，按 `-create_time` 排序分页。

- [ ] **Step 3: 实现清理时间读取与保存**

读取 `SystemSetting(type=SettingType.LOG)`，默认 `180`；保存 `clean_time` 到 `meta.clean_time`。

- [ ] **Step 4: 实现导出兜底**

复用分页查询过滤，返回当前过滤结果列表，避免前端导出接口 404。

### Task 3: 路由挂载

**Files:**
- Modify: `apps/system_manage/views/__init__.py`
- Modify: `apps/system_manage/urls.py`

- [ ] **Step 1: 导入 `log_management` 视图**

在 `views/__init__.py` 添加 `from .log_management import *`。

- [ ] **Step 2: 添加 URL**

添加：
`operate_log/menu_operation_option/`
`operate_log/get_clean_time`
`operate_log/save`
`operate_log/export/`
`operate_log/<int:current_page>/<int:page_size>`

### Task 4: 验证

**Files:**
- No code changes

- [ ] **Step 1: 运行语法检查**

运行 `python -m py_compile apps/system_manage/views/log_management.py apps/system_manage/tests.py`。

- [ ] **Step 2: 运行迁移检查**

运行 `python apps/manage.py makemigrations system_manage --check --dry-run`。

- [ ] **Step 3: 运行接口脚本**

用 `APIRequestFactory` 直接调用菜单、清理时间、分页查询和保存接口，确认响应结构。
