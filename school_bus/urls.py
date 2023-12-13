"""
URL configuration for school_bus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# 【URL和函数的对应关系】【常修改】

from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('login/', views.login),
    path('login/resetpwd/', views.reset_pwd),
    path('register/', views.register),
    path('user/', views.user),
    path('user/info/', views.user_info),
    path('user/account/', views.user_account),
    path('user/search/', views.search_route),
    path('user/search/buy/', views.buy),
    path('manager/', views.manager),
    path('manager/info/', views.manager_info),
    path('manager/manage_user/', views.manage_user),
    path('manager/manage_user/add/', views.manage_add_user),
    path('manager/manage_order/', views.manage_order),
    path('manager/manage_sche/', views.manage_sche),
    path('modify_user/', views.modify_user),
    path('modify_order/', views.modify_order),
    path('modify_sche/', views.modify_sche),
]
