from django.urls import path, include
from userprofiles import pwd

urlpatterns = [
    path('paswordd', pwd.change_password, name='change_password'),
    path('paswordd-done',pwd.change_password_done,name='change_password_done'),
]