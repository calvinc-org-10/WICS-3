from django.urls import path, include
from userprofiles.login import WICSLoginView
from userprofiles import pwd

urlpatterns = [
    path('login/', WICSLoginView.as_view(), name='login'),
    path('paswordd', pwd.change_password, name='change_password'),
    path('paswordd-done',pwd.change_password_done,name='change_password_done'),
]