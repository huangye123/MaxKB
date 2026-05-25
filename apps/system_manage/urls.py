from django.urls import path

from . import views

app_name = "system_manage"
# @formatter:off
# fmt: off
urlpatterns = [
    path('display/info', views.DisplayInfo.as_view()),
    path('workspace/<str:workspace_id>/application/<int:current_page>/<int:page_size>', views.WorkspaceApplicationPage.as_view()),
    path('workspace/<str:workspace_id>/user_resource_permission/user/<str:user_id>/resource/<str:resource>', views.WorkSpaceUserResourcePermissionView.as_view()),
    path('workspace/<str:workspace_id>/user_resource_permission/user/<str:user_id>/resource/<str:resource>/<int:current_page>/<int:page_size>', views.WorkSpaceUserResourcePermissionView.Page.as_view()),
    path('workspace/<str:workspace_id>/resource_user_permission/resource/<str:target>/resource/<str:resource>', views.WorkspaceResourceUserPermissionView.as_view()),
    path('workspace/<str:workspace_id>/resource_user_permission/resource/<str:target>/resource/<str:resource>/<int:current_page>/<int:page_size>', views.WorkspaceResourceUserPermissionView.Page.as_view()),
    path('workspace/<str:workspace_id>/resource_mapping/<str:resource>/<str:resource_id>/<int:current_page>/<int:page_size>', views.ResourceMappingView.as_view()),
    path('workspace/<str:workspace_id>/mapping_resource/<str:resource>/<str:resource_id>/<int:current_page>/<int:page_size>', views.MappingResourceView.as_view()),
    path('email_setting', views.SystemSetting.Email.as_view()),
    path('profile', views.SystemProfile.as_view()),
    path('auth/setting', views.SystemAuthView.Setting.as_view()),
    path('auth/connection', views.SystemAuthView.Connection.as_view()),
    path('platform/source', views.SystemAuthView.PlatformSource.as_view()),
    path('auth/<str:auth_type>/detail', views.SystemAuthView.Operate.as_view()),
    path('auth/<str:auth_type>/info', views.SystemAuthView.Operate.as_view()),
    path('chat_user/auth/connection', views.ChatUserAuthView.Connection.as_view()),
    path('chat_user/auth/platform/source', views.ChatUserAuthView.PlatformSource.as_view()),
    path('chat_user/auth/<str:auth_type>/detail', views.ChatUserAuthView.Operate.as_view()),
    path('chat_user/auth/<str:auth_type>/info', views.ChatUserAuthView.Operate.as_view()),
    path('operate_log/menu_operation_option/', views.OperateLogView.MenuOperationOption.as_view()),
    path('operate_log/get_clean_time', views.OperateLogView.CleanTime.as_view()),
    path('operate_log/save', views.OperateLogView.CleanTime.as_view()),
    path('operate_log/export/', views.OperateLogView.Export.as_view()),
    path('operate_log/<int:current_page>/<int:page_size>', views.OperateLogView.Page.as_view()),
    path('system/chat_user', views.SystemChatUser.as_view()),
    path('system/chat_user/list', views.SystemChatUser.List.as_view()),
    path('system/chat_user/user_manage/<int:current_page>/<int:page_size>', views.SystemChatUser.UserManagePage.as_view()),
    path('system/chat_user/<str:user_id>', views.SystemChatUser.Operate.as_view()),
    path('system/group', views.SystemGroup.as_view()),
    path('system/group/<str:group_id>/user_list/<int:current_page>/<int:page_size>', views.SystemGroup.UserListPage.as_view()),
    path('system/role', views.SystemRole.as_view()),
    path('system/role/<str:role_id>/permission', views.SystemRolePermission.as_view()),
    path('valid/<str:valid_type>/<int:valid_count>', views.Valid.as_view())
]
