HOSTNAME = "http://localhost:8380"

PAYPAL = {
  "USERID": "mhanso_1311195548_biz_api1.gmail.com",
  "PASSWORD": "1311195583",
  "SIGNATURE": "AcK70HpHQnaxn8HNvW3M8oi-gkPoAj7HObYK2oDKjgFiWebERXmCPF9A",
  "APPLICATIONID":  "APP-80W284485P519543T",
  
  #"RETURNURL": HOSTNAME + "/paypal/return",
  #"CANCELURL": HOSTNAME + "/paypal/cancel",
  "RETURNURL": HOSTNAME + "/paypal/embedded_return",
  "CANCELURL": HOSTNAME + "/paypal/embedded_cancel",
  "PREAPPROVAL_RETURNURL": HOSTNAME + "/paypal/preapproval_return",
  "PREAPPROVAL_CANCELURL": HOSTNAME + "/paypal/preapproval_cancel",
}
