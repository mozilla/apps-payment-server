from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('app.views',
    (r'^$', 'home'),
    url(r'^payment_succeeded$', 'payment_succeeded',
        name='app.payment_succeeded'),
)
