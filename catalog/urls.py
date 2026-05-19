from django.urls import path
from . import views

urlpatterns = [
    # الكتب
    path('books/', views.book_list_view, name='book_list'),
    path('books/add/', views.book_create_view, name='book_create'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_update_view, name='book_update'),
    path('books/<int:pk>/delete/', views.book_delete_view, name='book_delete'),

    # المؤلفون
    path('authors/', views.author_list_view, name='author_list'),
    path('authors/add/', views.author_create_view, name='author_create'),
    path('authors/<int:pk>/edit/', views.author_update_view, name='author_update'),

    # التصنيفات
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/add/', views.category_create_view, name='category_create'),

    # التقييمات
    path('reviews/', views.review_list_view, name='review_list'),
    path('reviews/<int:pk>/approve/', views.review_approve_view, name='review_approve'),
    path('reviews/<int:pk>/reject/', views.review_reject_view, name='review_reject'),
]