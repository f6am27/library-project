from django.urls import path
from . import views

urlpatterns = [
    # الاستعارة
    path('loans/', views.loan_list_view, name='loan_list'),
    path('loans/add/', views.loan_create_view, name='loan_create'),
    path('loans/<int:pk>/', views.loan_detail_view, name='loan_detail'),
    path('loans/<int:pk>/return/', views.loan_return_view, name='loan_return'),

    # الغرامات
    path('fines/', views.fine_list_view, name='fine_list'),
    path('fines/<int:pk>/pay/', views.fine_pay_view, name='fine_pay'),

    # الحجوزات
    path('reservations/', views.reservation_list_view, name='reservation_list'),
    path('reservations/add/', views.reservation_create_view, name='reservation_create'),
    path('reservations/<int:pk>/cancel/', views.reservation_cancel_view, name='reservation_cancel'),
 # الطلبات الجديدة
    path('requests/', views.request_list_view, name='request_list'),
    path('requests/<int:pk>/approve-loan/', views.request_approve_loan_view, name='request_approve_loan'),
    path('requests/<int:pk>/approve-sale/', views.request_approve_sale_view, name='request_approve_sale'),
    path('requests/<int:pk>/reject/', views.request_reject_view, name='request_reject'),

    path('visitor-loan/', views.visitor_loan_view, name='visitor_loan'),
    path('direct-sale/', views.direct_sale_view, name='direct_sale'),


]