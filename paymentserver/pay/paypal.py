import payprovider
import config
import urllib
import httplib
import urlparse
import logging

log = logging.getLogger("pay")


headers = {
  'Content-type':'application/x-www-form-urlencoded',
  'Accept':'text/plain',
  'X-PAYPAL-SECURITY-USERID': config.PAYPAL["USERID"],
  'X-PAYPAL-SECURITY-PASSWORD': config.PAYPAL["PASSWORD"],
  'X-PAYPAL-SECURITY-SIGNATURE': config.PAYPAL["SIGNATURE"],
  'X-PAYPAL-APPLICATION-ID': config.PAYPAL["APPLICATIONID"],
  'X-PAYPAL-SERVICE-VERSION':'1.1.0',
  'X-PAYPAL-REQUEST-DATA-FORMAT':'NV',
  'X-PAYPAL-RESPONSE-DATA-FORMAT':'NV'
}

def create():
  return PayPalProvider()
  
class PayPalProvider(object):

  def setupPayment(self, senderAddress, receiverAddress, amount, currencyCode, preappKey = None, returnTo = None):
    params = {
      'requestEnvelope.errorLanguage':'en_US',
      'returnUrl': (returnTo != None) and (config.HOSTNAME + returnTo) or config.PAYPAL["RETURNURL"],
      'cancelUrl': config.PAYPAL["CANCELURL"],
#      'senderEmail': senderAddress, cannot be included for digital goods
      'actionType':'PAY',
      'currencyCode': currencyCode,
      #'preapproval':'true',
      'feesPayer':'EACHRECEIVER',} # NB could have ipnNotificationUrl
            
    #Add Receivers            
    params.update({
      'receiverList.receiver(0).email': receiverAddress,
      'receiverList.receiver(0).amount': amount,
      'receiverList.receiver(0).primary':'false',
      'receiverList.receiver(0).paymentType':'DIGITALGOODS',
       })
                
    #Add Client Details
    params.update({            
      'clientDetails.ipAddress':'127.0.0.1',
      'clientDetails.deviceId':'mydevice',
      'clientDetails.applicationId':'PayNvpDemo',
      })
        
    if preappKey:
      params.update({
        'preapprovalkey': preappKey
      })
      ## TODO PIN
      
    enc_params = urllib.urlencode(params)  
    
    try:
      #Connect to sand box and POST.
      log.debug("Connecting to sandbox: %s" % params)
      conn = httplib.HTTPSConnection("svcs.sandbox.paypal.com")
      conn.request("POST", "/AdaptivePayments/Pay/", enc_params, headers)

      #Check the response - should be 200 OK.
      response = conn.getresponse()
      print (response.status, response.reason)

      #Get the reply and print it out.
      data = response.read()

      #Close the Connection.
      conn.close()

      result = (urlparse.parse_qs(data))
    except Exception, e:
      raise payprovider.PaymentException("Unable to set up payment: %s" % e)

    if result.has_key("responseEnvelope.ack"):
      if result["responseEnvelope.ack"][0] == "Failure":
        raise payprovider.PaymentException("Unable to set up payment: %s" % (result["error(0).message"]))
      elif result["responseEnvelope.ack"][0] == "Success":
        return payprovider.PendingPayment(result["payKey"][0], result["responseEnvelope.timestamp"][0])
      else:
        raise payprovider.PaymentException("Unexpected return value - responseEnvelope.ack was %s; %s" % (result["responseEnvelope.ack"], str(result)))
    else:
      raise payprovider.PaymentException("Unexpected return value - no responseEnvelope.ack; %s" % (str(result)))

    
  def setupPreapproval(self, senderAddress, maxTotal, currencyCode, startingDate, endingDate):
    params = {
      'requestEnvelope.errorLanguage':'en_US',
      'requestEnvelope.detailLevel':'ReturnAll',
      'returnUrl': config.PAYPAL["PREAPPROVAL_RETURNURL"],
      'cancelUrl': config.PAYPAL["PREAPPROVAL_CANCELURL"],
      #'senderEmail': senderAddress,
      'currencyCode': currencyCode,} # NB could have ipnNotificationUrl
            
    #Client Details
    #params.update({
    #           'clientDetails.applicationId':'PlatformPreview',
    #            'clientDetails.deviceId':'mydevice',
    #            'clientDetails.ipAddress':'127.0.0.1',
    #             })
                
    #PreApproval Details
    params.update({
      'maxTotalAmountOfAllPayments':maxTotal,
      'startingDate': startingDate.strftime("%Y-%m-%dT%H:%M:%S"), # '2010-07-25T07:00:00',
      'endingDate':endingDate.strftime("%Y-%m-%dT%H:%M:%S"),
    })
           
    enc_params = urllib.urlencode(params)  
    
    try:
      #Connect to sand box and POST.
      conn = httplib.HTTPSConnection("svcs.sandbox.paypal.com")
      conn.request("POST", "/AdaptivePayments/Preapproval/", enc_params, headers)

      #Check the response - should be 200 OK.
      response = conn.getresponse()
      print (response.status, response.reason)

      #Get the reply and print it out.
      data = response.read()

      #Close the Connection.
      conn.close()

      result = (urlparse.parse_qs(data))

    except Exception, e:
      raise payprovider.PaymentException("Unable to set up preapproval: %s" % e)

    if result.has_key("responseEnvelope.ack"):
      if result["responseEnvelope.ack"][0] == "Failure":
        raise payprovider.PaymentException("Unable to set up preapproval: %s" % (result["error(0).message"]))
      elif result["responseEnvelope.ack"][0] == "Success":
        return payprovider.PendingPreapproval(result["preapprovalKey"][0], result["responseEnvelope.timestamp"][0])
      else:
        raise payprovider.PaymentException("Unexpected return value - responseEnvelope.ack was %s; %s" % (result["responseEnvelope.ack"], str(result)))
    else:
      raise payprovider.PaymentException("Unexpected return value - no responseEnvelope.ack; %s" % (str(result)))

  def queryPreapproval(self, preappKey):
    params = {
      'requestEnvelope.errorLanguage':'en_US',
      'requestEnvelope.detailLevel':'ReturnAll',
      'preapprovalKey': preappKey
    }   
            
    #Client Details
    #params.update({
    #            'clientDetails.applicationId':'PlatformPreview',
    #            'clientDetails.deviceId':'mydevice',
    #            'clientDetails.ipAddress':'127.0.0.1',
    #             })
                
    enc_params = urllib.urlencode(params)  
    
    try:
      #Connect to sand box and POST.
      conn = httplib.HTTPSConnection("svcs.sandbox.paypal.com")
      conn.request("POST", "/AdaptivePayments/PreapprovalDetails", enc_params, headers)

      #Check the response - should be 200 OK.
      response = conn.getresponse()
      print (response.status, response.reason)

      #Get the reply and print it out.
      data = response.read()

      #Close the Connection.
      conn.close()

      result = (urlparse.parse_qs(data))

    except Exception, e:
      raise payprovider.PaymentException("Unable to set up preapproval: %s" % e)

    if result.has_key("responseEnvelope.ack"):
      if result["responseEnvelope.ack"][0] == "Failure":
        raise payprovider.PaymentException("Unable to set up preapproval: %s" % (result["error(0).message"]))
      elif result["responseEnvelope.ack"][0] == "Success":
        return result
      else:
        raise payprovider.PaymentException("Unexpected return value - responseEnvelope.ack was %s; %s" % (result["responseEnvelope.ack"], str(result)))
    else:
      raise payprovider.PaymentException("Unexpected return value - no responseEnvelope.ack; %s" % (str(result)))
    

# {'responseEnvelope.build': ['1971792'], 'responseEnvelope.timestamp': ['2011-07-20T14:01:36.252-07:00'],
#   'paymentExecStatus': ['CREATED'], 'payKey': ['AP-4M866000VR3031610'], 'responseEnvelope.correlationId': ['94a6c7d0ea57a'], 
#  'responseEnvelope.ack': ['Success']}
# {'error(0).domain': ['PLATFORM'], 'error(0).message': ['Authentication failed. API credentials are incorrect.'], 'responseEnvelope.build': ['1971792'], 'responseEnvelope.timestamp': ['2011-07-20T13:28:32.173-07:00'], 'responseEnvelope.correlationId': ['4d95dcb50efca'], 'error(0).subdomain': ['Application'], 'error(0).errorId': ['520003'], 'error(0).category': ['Application'], 'error(0).severity': ['Error'], 'responseEnvelope.ack': ['Failure']}
