"""
wattpad_reader project URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login / logout - sign up yoxdur, user-lar admin paneldən yaradılır
    path('login/', auth_views.LoginView.as_view(template_name='reader/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Reader app-ın öz URL-ləri
    path('', include('reader.urls')),
]
