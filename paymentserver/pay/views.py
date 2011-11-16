"""
Views for Firefox Pay

"""
import json

from django.views.generic.simple import *
from django import forms
from django.http import HttpResponse
import django.conf
from django.conf import settings
import models
import urlparse
import idassertion
import logging
import json
import datetime
import math
import config

import jwt

log = logging.getLogger("pay")
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

def get_account(email):
  return models.Account.objects.get_or_create(email=email)[0]

def home(request):
  acct = None
  if request.session.has_key("verified_email"):
    acct = get_account(request.session["verified_email"])
  return direct_to_template(request, 'index.html', {"acct":acct})

class LoginForm(forms.Form):
  assertion = forms.CharField()

def logout(request):
  if request.session.has_key("verified_email"):
    del request.session["verified_email"]

  if request.GET.has_key("return_to"):
    return HttpResponseRedirect("/" + request.GET["return_to"])
  else:
    return HttpResponseRedirect("/")

def login(request):
  if request.method == "POST":
    form = LoginForm(request.POST)
    if form.is_valid():
      usersid = form.cleaned_data["assertion"]
      try:
        email = idassertion.verify(usersid)
        request.session["verified_email"] = email

        if request.POST.has_key("return_to"):
          # XX beware of XSRF attacks here
          return HttpResponseRedirect("/" + request.POST["return_to"])
        else:
          return HttpResponseRedirect("/")
      except Exception, e:
        # bad login!
        return direct_to_template(request, 'login_error.html', {"message":"Invalid user identity: %s (%s)" % (e, usersid)})
    else:
      # bad form!
      return direct_to_template(request, 'login_error.html', {"message":"Invalid form submission"})
  else:
    return direct_to_template(request, 'index.html')

def account(request):
  if not request.session.has_key("verified_email"):
    return HttpResponseRedirect("/")
  try:
    acct = get_account(request.session["verified_email"])
    return direct_to_template(request, 'account.html', {"acct":acct})
  except Exception, e:
    log.exception(e)
    return HttpResponseRedirect("/")


def start_payment(request):
  if True or request.session.has_key("verified_email"): # fake out session for now
    if request.method == "POST":
      try:
        # HACK fake out sender
        # acct = get_account(request.session["verified_email"])
        if not request.POST.has_key("sender"):
          return direct_to_template(request, 'error.html', {"errormsg": "Missing required parameter receiver"})
        acct = models.Account.objects.get_or_create(email=request.POST["sender"])[0]

        if not request.POST.has_key("receiver"):
          return direct_to_template(request, 'error.html', {"errormsg": "Missing required parameter receiver"})
        if not request.POST.has_key("amount"):
          return direct_to_template(request, 'error.html', {"errormsg": "Missing required parameter amount"})
        if not request.POST.has_key("cc"):
          return direct_to_template(request, 'error.html', {"errormsg": "Missing required parameter cc"})

        log.debug("Starting payment constructor")
        payment = models.Payment(account=acct, receiver=request.POST["receiver"], amount=request.POST["amount"], currencyCode=request.POST["cc"])
        log.debug("Calling payment setup")

        # Bah, this is really slow.  Tornado/twisted/Node FTW?
        payment.setup()
        if payment.processing_error:
          # whoops, didn't work
          return direct_to_template(request, 'error.html', {"errormsg": payment.processing_error})
        else:
          if payment.isComplete():
            # Had preapproval, hooray
            return HttpResponseRedirect(config.PAYPAL["RETURNURL"])
          else:
            # No preapproval; go ask
            return HttpResponseRedirect("https://www.sandbox.paypal.com/webapps/adaptivepayment/flow/pay?paykey=%s" % payment.provider_key)
            # If it's not DIGITALGOODS, we go here:
            # return HttpResponseRedirect("https://www.sandbox.paypal.com/webscr?cmd=_ap-payment&paykey=%s" % payment.provider_key)
      except Exception, e:
        return direct_to_template(request, 'error.html', {"errormsg": e})
    else:
      try:
        # acct = get_account(request.session["verified_email"]) fake out account for now
        return direct_to_template(request, 'payment_setup.html')
      except:
        return direct_to_template(request, 'error.html', {"errormsg": "Must have an account"})
  else:
    return direct_to_template(request, 'error.html', {"errormsg": "Must be logged in"})


def start_embedded_payment(request):
  return direct_to_template(request, 'embedded.html')


def get_embedded_payment_form(request):
  return direct_to_template(request, 'embedded_paypal_form.html')


def init_embedded_payment(request):
  if True or request.session.has_key("verified_email"): # fake session
    if request.method == "POST":
      try:
        log.debug("initializing embedded payment")
        # XXX HACK fake out sender
        # acct = get_account(request.session["verified_email"])
        if not request.POST.has_key("sender"):
          return HttpResponse({"status": "failure", "errormsg": "Missing required 'sender'"}, mimetype='application/json')
        acct = models.Account.objects.get_or_create(email=request.POST["sender"])[0]

        if not request.POST.has_key("receiver"):
          return HttpResponse({"status": "failure", "errormsg": "Missing required 'receiver'"}, mimetype='application/json')
        if not request.POST.has_key("amount"):
          return HttpResponse({"status": "failure", "errormsg": "Missing required 'amount'"}, mimetype='application/json')
        if not request.POST.has_key("cc"):
          return HttpResponse({"status": "failure", "errormsg": "Missing required 'cc'"}, mimetype='application/json')

        log.debug("Starting payment constructor for embedded payment")
        payment = models.Payment(account=acct, receiver=request.POST["receiver"], amount=request.POST["amount"], currencyCode=request.POST["cc"])
        log.debug("Calling payment setup for embedded payment")

        # Bah, this is really slow.  Tornado/twisted/Node FTW?
        payment.setup()
        if payment.processing_error:
          # whoops, didn't work
          log.debug("Processing error: %s" %payment.processing_error )
          return HttpResponse({"status": "failure", "errormsg": payment.processing_error}, mimetype='application/json')
        else:
          log.debug("Set up a payment; provider key is %s, preapproval is %s" % (payment.provider_key, payment.preapproval_key))
          result = {"paykey": payment.provider_key}
          if payment.preapproval_key:
              result["preapprovalKey"] = payment.preapproval_key

          return HttpResponse(json.dumps(result), mimetype='application/json')
      except Exception, e:
        log.exception(e)
        return HttpResponse({"status": "failure", "errormsg": e}, mimetype='application/json')
    else:
      return HttpResponse(status=405)
  else:
    log.debug("user is not logged in")
    return HttpResponse({"status": "failure", "errormsg": "User must be logged in"}, mimetype='application/json')

def paypal_embedded_return(request):
  if True or request.session.has_key("verified_email"):
    try:
      #acct = models.Account.objects.filter(email=request.session["verified_email"]).get()
      #log.info("paypal_embedded_return called")
      return direct_to_template(request, 'embedded_return.html')
    except Exception, e:
      pass
  else:
    log.error("paypal_return called with no session")

def paypal_embedded_cancel(request):
  if True or request.session.has_key("verified_email"):
    try:
      #acct = models.Account.objects.filter(email=request.session["verified_email"]).get()
      #log.info("paypal_embedded_cancel called")
      return direct_to_template(request, 'embedded_cancel.html')
    except Exception, e:
      pass
  else:
    log.error("paypal_cancel called with no session")


def start_preapproval(request):
  if True or request.session.has_key("verified_email"):
    if request.method == "POST":
      try:
        # HACK XXX fake out sender
        # acct = get_account(request.session["verified_email"])
        if not request.POST.has_key("sender"):
          return direct_to_template(request, 'error.html', {"errormsg": "Missing required parameter receiver"})
        acct = models.Account.objects.get_or_create(email=request.POST["sender"])[0]

        if not request.POST.has_key("amount"):
          return direct_to_template(request, 'error.html', {"errormsg": "Missing required parameter receiver"})

        log.debug("Starting payment constructor")

        # XXX this should be unique on user

        preapproval = models.Preapproval(account=acct, amount=request.POST["amount"])
        log.debug("Calling payment setup")

        # Bah, this is really slow.  Tornado/twisted/Node FTW?
        preapproval.setup()
        if preapproval.processing_error:
          # whoops, didn't work
          return direct_to_template(request, 'error.html', {"errormsg": preapproval.processing_error})
        else:
          return HttpResponseRedirect("https://www.sandbox.paypal.com/webscr?cmd=_ap-preapproval&preapprovalkey=%s" % preapproval.provider_key)
      except Exception, e:
        return direct_to_template(request, 'error.html', {"errormsg": e})
    else:
      try:
        #acct = get_account(request.session["verified_email"]) fake out account for now
        return direct_to_template(request, 'preapproval_setup.html')
      except:
        return direct_to_template(request, 'error.html', {"errormsg": "Must have an account"})
  else:
    return direct_to_template(request, 'error.html', {"errormsg": "Must be logged in"})


def paypal_return(request):
  if True or request.session.has_key("verified_email"):
    try:
      #acct = models.Account.objects.filter(email=request.session["verified_email"]).get()
      #log.info("paypal_return called")
      return direct_to_template(request, 'payment_return.html')
    except Exception, e:
      pass
  else:
    log.error("paypal_return called with no session")

def paypal_cancel(request):
  if True or request.session.has_key("verified_email"):
    try:
      #acct = models.Account.objects.filter(email=request.session["verified_email"]).get()
      #log.info("paypal_cancel called")
      return direct_to_template(request, 'payment_cancel.html')
    except Exception, e:
      pass
  else:
    log.error("paypal_cancel called with no session")



def paypal_preapproval_return(request):
  if True or request.session.has_key("verified_email"):
    try:
      #acct = models.Account.objects.filter(email=request.session["verified_email"]).get()
      #log.info("paypal_preapproval_return called")
      return direct_to_template(request, 'preapproval_return.html')
    except Exception, e:
      pass
  else:
    log.error("paypal_return called with no session")

def paypal_preapproval_cancel(request):
  if True or request.session.has_key("verified_email"):
    try:
      #acct = models.Account.objects.filter(email=request.session["verified_email"]).get()
      #log.info("paypal_preapproval_cancel called")
      return direct_to_template(request, 'preapproval_cancel.html')
    except Exception, e:
      pass
  else:
    log.error("paypal_cancel called with no session")

def preapproval_query(request):
  if True or request.session.has_key("verified_email"):
    preapp = None
    queryResult = None
    acct = None
    try:
      ### XXX HACK for sandbox - fake out sender
      # acct = models.Account.objects.filter(email=request.session["verified_email"]).get()
      if request.GET.has_key("sender"):
        acct = models.Account.objects.get_or_create(email=request.GET["sender"])[0]
      else:
        return direct_to_template(request, 'preapproval_status.html', {"acct":None, "preapp":None, "queryResult":None, "promptFakeSender":True})
      preapp = models.Preapproval.objects.filter(account=acct).get()
      queryResult = preapp.queryStatus()
    except models.Account.DoesNotExist, e:
      pass
    except models.Preapproval.DoesNotExist, e:
      pass
    return direct_to_template(request, 'preapproval_status.html', {"acct":acct, "preapp":preapp, "queryResult":queryResult, "promptFakeSender":False})
  else:
    return HttpResponseRedirect("/")


def as_json(handler):
  def makejson(*args, **kwargs):
    try:
      res = handler(*args, **kwargs)
    except:
      log.exception('Exception:')
      raise
    return HttpResponse(json.dumps(res),
                        mimetype='application/json',
                        status=200 )
  return makejson


def decode_request(signed_request):
  app_req = jwt.decode(signed_request, verify=False)
  app_req = json.loads(app_req)
  secret =  settings.APP_SECRETS[app_req['iss']]  # iss is the app key
  jwt.decode(signed_request, secret, verify=True)
  return app_req


@as_json
def start_app_payment(request):
  app_req = decode_request(str(request.POST['signed_request']))
  # pretend this is after:
  #   - user gets logged in through browser ID
  #   - transaction is started, user ID is part of transaction
  return {'valid': True, 'request': app_req['request'],
          'transaction_id': 1234}


@as_json
def submit_app_payment(request):
  app_req = decode_request(str(request.POST['signed_request']))
  # pretend it went through successfully!
  # this means the transaction is *pending*
  return {'successful': True, 'transaction_id': 1234,
          'request': app_req['request']}
