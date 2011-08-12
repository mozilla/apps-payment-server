import base64
## We export this import because simplejson (which has speedups) is
## generally preferrable to the API-compatible builtin json module
try:
    import simplejson as json
except ImportError:
    import json

def verify(assertion):
  """Verifies the assertion; returns the email if it
  is valid or raises InvalidIdentityAssertion."""
  parts = assertion.split(".")
  
  # base64.urlsafe_b64decode doesn't seem to understand the
  # padding-stripping convention.  adding == to make it happy.
  #print parts
  #print base64.b64decode(parts[0] + "===")
  #print base64.b64decode(parts[1] + "===")
  
  decoded_payload = base64.b64decode(parts[1] + "==")
  parsed_payload = json.loads(decoded_payload)
  return parsed_payload["email"]


class InvalidIdentityAssertion(Exception):
  pass