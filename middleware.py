# middleware.py
from django.conf import settings as django_settings
import import_string
from django.utils.deprecation import MiddlewareMixin


WICSurl = '/WICSdmm/'
WICSdbreq = {
    'dev': 'dev',
    'prod': 'prod',
    'demo': 'dmm',
}
WICSdb = {
    'dev': 'dev',
    'prod': 'prod',
    'demo': 'demo',
}

class DatabaseRouterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'GET' and not hasattr(request,'use_database'):
            path = request.path
            if path.startswith(WICSurl):
                request.use_database = WICSdb['demo']
            else:
                request.use_database = 'default'  # Fallback or handle differently if necessary

        response = self.get_response(request)
        return response


class RequestMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        for db_router in django_settings.DATABASE_ROUTERS:
            # pylint: disable-next=E1102
            router = import_string(db_router)
            if hasattr(router, 'set_request'):
                router.set_request(router, request)
        return None