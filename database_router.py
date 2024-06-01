# database_router.py (update)

class DatabaseRouter:
    request = None

    def set_request(self, request):
        self.request = request

    def db_for_read(self, model, **hints):
        if self.request and hasattr(self.request, 'use_database'):
            return self.request.use_database
        return 'default'

    def db_for_write(self, model, **hints):
        if self.request and hasattr(self.request, 'use_database'):
            return self.request.use_database
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True