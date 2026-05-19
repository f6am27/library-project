from django.urls import path
from . import views

urlpatterns = [
    # المصادقة
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # المنتسبون
    path('members/', views.member_list_view, name='member_list'),
    path('members/add/', views.member_create_view, name='member_create'),
    path('members/<int:pk>/', views.member_detail_view, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_update_view, name='member_update'),
    path('members/<int:pk>/suspend/', views.member_suspend_view, name='member_suspend'),

    # الإداريون (Super Admin فقط)
    path('admins/', views.admin_list_view, name='admin_list'),
    path('admins/add/', views.admin_create_view, name='admin_create'),
    path('admins/<int:pk>/delete/', views.admin_delete_view, name='admin_delete'),
]