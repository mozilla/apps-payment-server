from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('app.views',
    (r'^$', 'home'),
)
