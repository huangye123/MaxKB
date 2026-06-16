# 开发调试关键点

本文档记录当前项目在本地开发、接口适配和页面联调时确认过的关键点。

## 后端运行环境

- 本地后端调试入口使用 `backend_debug_runserver.py`。
- 调试服务监听 `0.0.0.0:8080`，前端通过 Vite 代理访问 `/admin/api`。
- 数据库和 Redis 不在本机，均使用服务器 `172.16.2.103`。
- 本地命令行验证接口、解密逻辑或 Django 测试时，要显式使用同一套环境变量：

```powershell
$env:MAXKB_CONFIG_TYPE='ENV'
$env:MAXKB_DB_NAME='maxkb'
$env:MAXKB_DB_HOST='172.16.2.103'
$env:MAXKB_DB_PORT='5432'
$env:MAXKB_DB_USER='root'
$env:MAXKB_DB_PASSWORD='Password123@postgres'
$env:MAXKB_REDIS_HOST='172.16.2.103'
$env:MAXKB_REDIS_PORT='6379'
$env:MAXKB_REDIS_PASSWORD='Password123@redis'
$env:MAXKB_REDIS_DB='0'
```

不要使用 `127.0.0.1` 验证依赖 DB/Redis 的行为，否则 RSA 密钥、缓存 token、登录状态等结果会和页面联调不一致。

## 后端服务重启

`backend_debug_runserver.py` 使用 `--noreload`，修改后端代码后需要重启服务才能生效。

```powershell
$processes = Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -like '*backend_debug_runserver.py*' -and $_.ProcessId -ne $PID
}
$processes | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Process -FilePath .\.venv\Scripts\python.exe `
  -ArgumentList @('backend_debug_runserver.py') `
  -WorkingDirectory 'F:\Project\NSLIB\MaxKB-PageIndex-Hybrid' `
  -WindowStyle Hidden
```

## 前端代理

- 页面请求地址通常是 `http://localhost:3000/admin/api/...`。
- Vite 代理会把 `/admin/api` 转发到后端 `http://127.0.0.1:8080`。
- 后端接口验证建议同时测两条路径：

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8080/admin/api/provider'
Invoke-RestMethod -Uri 'http://localhost:3000/admin/api/provider'
```

## 已适配的兼容接口

以下接口用于兼容当前前端页面请求，部分接口允许匿名访问，避免页面携带过期 token 时被认证层拦截成 `1002 Login expired`。

- `GET /admin/api/provider`
- `GET /admin/api/system/group`
- `GET /admin/api/system/chat_user/user_manage/1/20`
- `POST /admin/api/user/logout`
- `GET /admin/api/login/auth/setting`

已验证的典型响应：

```json
{"code":200,"message":"Success","data":true}
```

```json
{"code":200,"message":"Success","data":{"total":0,"records":[],"current":1,"size":20}}
```

## 登录 encryptedData 调试

系统登录页会先通过 `user.profile()` 获取 `rsaKey`，然后用该公钥加密登录表单：

```ts
const jsonData = JSON.stringify(loginForm.value)
const encryptedBase64 = js.encrypt(jsonData)
login.asyncLogin({ encryptedData: encryptedBase64, username: loginForm.value.username })
```

后端登录逻辑使用 `common.utils.rsa_util.decrypt()` 根据 DB/Redis 中的 RSA 私钥解密 `encryptedData`。

如果解密结果为空字符串 `''`，说明密文不是用当前后端公钥加密的，常见原因是：

- 前端拿到的 `rsaKey` 来自另一套后端或另一套 DB/Redis。
- 后端调试服务没有使用 `172.16.2.103` 的 DB/Redis。
- 修改环境变量后没有重启 `backend_debug_runserver.py`。
- Vite `adminApiMockPlugin()` 拦截了 `GET /admin/api/profile` 并返回硬编码 RSA 公钥。登录请求会继续转发到真实后端，导致“假公钥加密、真实私钥解密”，后端解密结果为空。`/admin/api/profile` 不应使用 mock。

## 本地 PE 展示 Mock

如仅需本地联调 PE 页面展示，可以在 `ui/env/.env` 中使用：

```env
VITE_DEV_UI_MOCK_LICENSE=true
```

该开关只在 Vite dev server 中处理 `GET /admin/api/profile`，先请求真实后端，再只覆盖：

```json
{"edition":"PE","license_is_valid":true}
```

`rsa` 必须透传真实后端返回值，不能 mock；否则登录页会使用错误公钥加密，导致 `/admin/api/user/login` 解密失败。当前本地开发默认开启该展示 mock；不能用于生产授权控制。

可用下面命令确认某段密文是否能被当前后端环境解开：

```powershell
$env:MAXKB_CONFIG_TYPE='ENV'
$env:MAXKB_DB_HOST='172.16.2.103'
$env:MAXKB_DB_NAME='maxkb'
$env:MAXKB_DB_PORT='5432'
$env:MAXKB_DB_USER='root'
$env:MAXKB_DB_PASSWORD='Password123@postgres'
$env:MAXKB_REDIS_HOST='172.16.2.103'
$env:MAXKB_REDIS_PORT='6379'
$env:MAXKB_REDIS_PASSWORD='Password123@redis'
$env:MAXKB_REDIS_DB='0'

.\.venv\Scripts\python.exe apps\manage.py shell -c "from common.utils.rsa_util import decrypt; print(repr(decrypt('<encryptedData>')))"
```

解密成功时应得到包含 `username`、`password` 等字段的 JSON 字符串；如果是 `''`，应先检查环境和服务重启，而不是继续从登录校验错误排查。

## 测试命令

常用后端测试命令：

```powershell
.\.venv\Scripts\python.exe apps\manage.py test users
.\.venv\Scripts\python.exe apps\manage.py test system_manage
.\.venv\Scripts\python.exe apps\manage.py test models_provider
```

测试输出中目前存在的已知 warning：

- `pydub` 找不到 `ffmpeg`。
- `ui/dist` 静态目录不存在。
- `oss` URL route/namespace warning。

这些 warning 不代表本次适配接口失败，判断结果以测试最终 `OK` 和手工接口响应为准。
