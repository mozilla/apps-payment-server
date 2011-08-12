class PendingPayment(object):
  def __init__(self, key, timestamp):
    self.key = key
    self.timestamp = timestamp

class PendingPreapproval(object):
  def __init__(self, key, timestamp):
    self.key = key
    self.timestamp = timestamp
    
class PaymentException(Exception):
  def __init__(self, message):
    self.msg = message
    
  def __str__(self):
    return "<PaymentException: %s>" % self.msg  

  def __repr__(self):
    return "<PaymentException: %s>" % self.msg