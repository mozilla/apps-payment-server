from django.db import models
import datetime, uuid
import paypal as payprovider
import logging

log = logging.getLogger("pay")


PaymentProvider = payprovider.create()

class UUIDObject(models.Model):
  # use a custom built primary key so that we have an
  # easier time testing against remote systems
  id = models.CharField(max_length=50, primary_key=True)

  def save(self, *args, **kwargs):
    if not self.id:
      self.id = str(uuid.uuid1())
      
    super(UUIDObject,self).save(*args, **kwargs)
      
  # we don't actually want to instantiate a table for this model
  class Meta:
    abstract = True
  
class Account(UUIDObject):
  email = models.EmailField(unique=True)
  first_name = models.CharField(max_length=100)
  last_name = models.CharField(max_length=100)
  
  # prepproval code...
  #cc_number = models.CharField(max_length=30, null=True)
  #cc_expiration = models.CharField(max_length=5, null=True)  
  #provider_created_at = models.DateTimeField(null=True)
  
  def __repr__(self):
    return "<Account %s>" % self.email

  def __str__(self):
    return "<Account %s>" % self.email

class Payment(UUIDObject):
  account = models.ForeignKey(Account)
  receiver = models.EmailField()
  amount = models.DecimalField(max_digits = 6, decimal_places = 2)
  currencyCode = models.CharField(max_length=6)

  provider_key = models.CharField(max_length=100, null=True)
  preapproval_key = models.CharField(max_length=100, null=True) # technically we don't have to save this, just being complete
  return_to= models.CharField(max_length=100, null=True) # XXX this is stupid, should just have a boolean for whether it was lightboxed

  # log the steps
  created_at = models.DateTimeField(auto_now_add=True)
  setup_started_at = models.DateTimeField(null=True)
  setup_succeeded_at = models.DateTimeField(null=True)
  user_approved_at = models.DateTimeField(null=True)
  completed_at = models.DateTimeField(null=True)

  processing_failed_at = models.DateTimeField(null=True)
  processing_error = models.TextField(null=True)

  def isComplete(self):
    return self.completed_at != None

  def setup(self):
    log.debug("Start payment setup")
    self.setup_started_at = datetime.datetime.utcnow()
    try:
      # if there is already a preapproval for this account, use it
      preapp = None
      try:
        preapp = Preapproval.objects.filter(account=self.account).get()
        log.debug("Got a preapproval key: " + preapp.provider_key)
      except Preapproval.DoesNotExist, e:
        log.debug("No preapproval key")
        pass
        
      ### XXX need to deal with preapproval over the limit
      preappKey = None
      if preapp:
        preappKey = preapp.provider_key
        self.preapproval_key = preappKey
      
      pendingPayment = PaymentProvider.setupPayment(self.account.email, self.receiver, self.amount, 
        self.currencyCode, preappKey = preappKey, returnTo=self.return_to)
      
      log.debug("Finished setup payment")
      self.provider_key = pendingPayment.key
      self.setup_succeeded_at = datetime.datetime.utcnow()
      #if preapp:
      #  self.completed_at = datetime.datetime.utcnow()
      self.save()
        
    except Exception, e:
      log.error("Payment setup failed: %s" % str(e))
      log.exception(e)
      self.processing_failed_at = datetime.datetime.utcnow()
      self.processing_error = str(e)

  def approved(self):
    # meaning that the SENDER has approved - not that the PROVIDER has approved it
    self.approved_at = datetime.datetime.utcnow()
    self.save()
    
  def complete(self):
    self.completed_at = datetime.datetime.utcnow()
    self.save()



class Preapproval(UUIDObject):
  account = models.ForeignKey(Account)
  amount = models.IntegerField()
  provider_key = models.CharField(max_length=100, null=True)
  
  # log the steps
  created_at = models.DateTimeField(auto_now_add=True)
  setup_started_at = models.DateTimeField(null=True)
  setup_succeeded_at = models.DateTimeField(null=True)
  user_approved_at = models.DateTimeField(null=True)
  completed_at = models.DateTimeField(null=True)

  processing_failed_at = models.DateTimeField(null=True)
  processing_error = models.TextField(null=True)

  def isComplete(self):
    return self.completed_at != None

  def setup(self):
    log.debug("Start preapproval setup")
    self.setup_started_at = datetime.datetime.utcnow()
    try:
      pendingPreapproval = PaymentProvider.setupPreapproval(self.account.email, self.amount, "USD", datetime.datetime.utcnow(), datetime.datetime.utcnow() +datetime.timedelta(days=365))
      log.debug("Finished setup preapproval")
      self.provider_key = pendingPreapproval.key
      self.setup_succeeded_at = datetime.datetime.utcnow()
      self.save()
    except Exception, e:
      log.error("Preapproval setup failed: %s" % str(e))
      log.exception(e)
      self.processing_failed_at = datetime.datetime.utcnow()
      self.processing_error = str(e)

  def queryStatus(self):
    return PaymentProvider.queryPreapproval(self.provider_key)

  def approved(self):
    # meaning that the SENDER has approved - not that the PROVIDER has approved it
    self.approved_at = datetime.datetime.utcnow()
    self.save()
    
  def complete(self):
    self.completed_at = datetime.datetime.utcnow()
    self.save()

