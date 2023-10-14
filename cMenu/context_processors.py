from django.conf import settings as django_settings # import the settings file

def settings_template_var(req):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'DJANGO_SETTINGS': django_settings}