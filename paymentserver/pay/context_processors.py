from django.conf import settings

def base(request):
    return {'settings': settings}
