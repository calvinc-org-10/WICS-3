from django.urls import path, include
from userprofiles.login import WICSLoginView
from userprofiles import pwd
from WICS import WICSdown


urlpatterns = [
    path('login/', WICSLoginView.as_view(), name='login'),
    # path('login/', WICSdown.WICSdown , name='WICSdown'),       # this is actually the entry point to WICS
    path('paswordd', pwd.change_password, name='change_password'),
    path('paswordd/u/<str:usNm>', pwd.change_password, name='change_password_u'),
    path('paswordd-done/<str:usNm>',pwd.change_password_done,name='change_password_done'),
    path('paswordd-done/00',pwd.change_password_deny,name='change_password_deny'),
]