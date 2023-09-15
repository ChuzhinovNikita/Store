from django.urls import path
from . import views

urlpatterns = [
    path('log_in/', views.log_in, name='log_in'),
    path('register/', views.register, name='register'),
    path('log_out/', views.log_out, name='log_out'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('reset_password/', views.reset_password, name='reset_password'),
]
