"""
URL configuration for MySurvey project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from app.views import SurveyManagementView, CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', SurveyManagementView.as_view(), name='main_page'),  # Use 'main_page' as the name
    path('qr_code/', include('qr_code.urls', namespace='qr_code')),
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('accounts/', include('allauth.urls')),
    path('surveys/', include('app.urls')),  # Include other survey-related URLs
]
