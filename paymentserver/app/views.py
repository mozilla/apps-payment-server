
from django.shortcuts import render


def home(request):
    all_products = [Product(code='glasses',
                            description='Virtual 3D Glasses',
                            price=3.99),
                    Product(code='shoes',
                            description='Virtual Shoes',
                            price=2.99)]
    return render(request, 'app/home.html', {'all_products': all_products})


class Product(object):

    def __init__(self, price=0.0, code='', description=''):
        self.price = price
        self.code = code
        self.description = description
