from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Customers
    path('customers/', views.customers_list, name='customers_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Sales
    path('sales/', views.sales_list, name='sales_list'),
    path('sales/export/', views.sales_export, name='sales_export'),
    path('sales/add/', views.sale_add, name='sale_add'),
    path('sales/<int:pk>/edit/', views.sale_edit, name='sale_edit'),
    path('sales/<int:pk>/delete/', views.sale_delete, name='sale_delete'),

    # Debts
    path('debts/', views.debts_list, name='debts_list'),
    path('debts/add/', views.debt_add, name='debt_add'),
    path('debts/<int:pk>/edit/', views.debt_edit, name='debt_edit'),
    path('debts/<int:pk>/paid/', views.debt_mark_paid, name='debt_mark_paid'),
    path('debts/<int:pk>/delete/', views.debt_delete, name='debt_delete'),

    # Expenses
    path('expenses/', views.expenses_list, name='expenses_list'),
    path('expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),

    # Income
    path('income/', views.income_list, name='income_list'),
    path('income/add/', views.income_add, name='income_add'),
    path('income/<int:pk>/edit/', views.income_edit, name='income_edit'),
    path('income/<int:pk>/delete/', views.income_delete, name='income_delete'),

    # Staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_add, name='staff_add'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),
]
