from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import views as auth_views
from cMenu.utils import is_user_in_group


def WICSlogout(req:HttpRequest) -> HttpResponse:
    return auth_views.logout_then_login(req,login_url=reverse('login' if not is_user_in_group(req.user,'demo') else 'WICSdemoLogin'))