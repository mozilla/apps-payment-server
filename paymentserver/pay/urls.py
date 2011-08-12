from django.conf.urls.defaults import *

from django.conf import settings

from views import *

urlpatterns = patterns(
    '',
    (r'^$', home),
    (r'^login$', login),
    (r'^logout$', logout),
    (r'^account$', account),

    (r'^start_payment$', start_payment),
    (r'^start_preapproval$', start_preapproval),
    (r'^start_embedded_payment$', start_embedded_payment),
    (r'^init_embedded_payment$', init_embedded_payment),
    
    (r'^paypal/return$', paypal_return),
    (r'^paypal/cancel$', paypal_cancel),
    (r'^paypal/preapproval_return$', paypal_preapproval_return),
    (r'^paypal/preapproval_cancel$', paypal_preapproval_cancel),
    (r'^paypal/embedded_return$', paypal_embedded_return),
    (r'^paypal/embedded_cancel$', paypal_embedded_cancel),
    (r'^preapproval_status$', preapproval_query),
    


    # static
    # FIXME: NEED TO REPLACE THIS with django 1.3 goodness at some point
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': '%s/pay/static' % settings.PROJECT_HOME}),    

)
