from django.urls import reverse
from django.contrib.auth import views as auth_views


def WICSlogout(req):
    return auth_views.logout_then_login(req,login_url=reverse('login'))