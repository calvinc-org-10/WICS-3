"""django_support URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import include, path
from userprofiles import log_in


urlpatterns = [
    # path('', include("cMenu.load_data.load_orig_cMenu")),
    # path('', include("WICS.load_data.load_L6_Materials")),
    # path('', include("port001")),
    path('', log_in.loginbegin,name='log_in'), # to become obsolete once migrated to django authentication
    path('_c_u_s_r',log_in.checkuser,name='checkuser'), # to become obsolete once migrated to django authentication
    path('menu/', include("cMenu.urls")),
    path('WICS/', include("WICS.urls")),
    path('admin/',admin.site.urls),
    path('akntt/',include("userprofiles.urls")),
    path('akntt/',include("django.contrib.auth.urls")),
]