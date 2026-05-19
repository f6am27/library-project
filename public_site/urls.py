from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('books/', views.book_list_view, name='public_book_list'),
    path('books/<int:pk>/', views.book_detail_view, name='public_book_detail'),
    path('books/<int:pk>/request/', views.book_request_view, name='book_request'),
    path('about/', views.about_view, name='about'),
    path('member/login/', views.member_login_view, name='member_login'),
    path('member/logout/', views.member_logout_view, name='member_logout'),
    path('member/dashboard/', views.member_dashboard_view, name='member_dashboard'),
]