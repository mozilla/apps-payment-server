import calendar
from decimal import Decimal
import json
import time

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import jwt


def home(request):
    all_products = [Product(code='glasses',
                            name='Virtual 3D Glasses',
                            description='Virtual 3D Glasses',
                            price=Decimal('0.99')),
                    Product(code='shoes',
                            name='Virtual Shoes',
                            description='Virtual Shoes',
                            price=Decimal('0.99'))]
    return render(request, 'app/home.html', {'all_products': all_products})


@csrf_exempt
def payment_succeeded(request):
    pass


class Product(object):

    def __init__(self, price=0.0, code='', name='', description=''):
        self.price = price
        self.code = code
        self.name = name
        self.description = description
        iat = calendar.timegm(time.gmtime())
        exp = iat + 3600  # expires in 1 hour
        request = json.dumps({
            'iss': settings.APP_OPERATOR_KEY,
            'aud': "marketplace.mozilla.org",
            'typ': "mozilla/payments/pay/v1",
            'exp': exp,
            'iat': iat,
            'request': {
                'price': str(self.price),
                'currency': "USD",
                'name': self.name,
                'description': self.description,
                'productdata': "ABC123_DEF456_GHI_789.XYZ"
            }
        })
        self.request_data = jwt.encode(request, settings.APP_OPERATOR_SECRET,
                                       algorithm='HS256')
