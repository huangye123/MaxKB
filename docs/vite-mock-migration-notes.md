# Vite Mock Migration Notes

The following `ui/vite.config.ts` development mocks have been migrated to backend compatibility endpoints:

- `GET /admin/api/display/info`
- `GET /admin/api/workspace/default/APPLICATION/folder`
- `GET /admin/api/workspace/default/application/1/30`
- `GET /admin/api/user/profile`

These requests now go through the Vite `/admin/api` proxy to the backend. The backend compatibility views use anonymous authentication, so a stale `Authorization` header does not produce `1002 Login expired`.

`GET /admin/api/user/profile` now uses the real backend `UserProfileView` response. It must be called with a valid login token and returns roles and permissions from the backend authentication context instead of a hardcoded Vite JSON fixture.

No admin API response mock or license overlay is kept in Vite dev behavior. `GET /admin/api/profile` now goes through the backend unchanged, including `edition`, `license_is_valid`, and `rsa`.
