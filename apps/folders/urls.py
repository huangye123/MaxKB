from django.urls import path

from . import views

app_name = "folder"
urlpatterns = [
    path('workspace/<str:workspace_id>/APPLICATION/folder', views.WorkspaceApplicationFolder.as_view()),
    path('workspace/<str:workspace_id>/<str:source>/folder', views.FolderView.as_view()),
    path('workspace/<str:workspace_id>/<str:source>/folder/<str:folder_id>', views.FolderView.Operate.as_view()),
]
