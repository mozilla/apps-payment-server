Design Notes on an In-App Payments API:
========================================

The goal of an in-app payments API is to allow web content to initiate a payment from the user to a web application, with these properties:

1. The application does not receive any payment card data from the user
2. The user is only required to enter her payment card data once (shall we say, "per account" - but somewhere on the order of once a year or less)
3. The payment card data is stored in a way that satisfies PCI DSS requirements
4. The user receives clear, cancellable confirmation of what the payment will entail, from a non-spoofable source.
5. The application receives clear, non-repudiatable confirmation that a payment has been completed, and has an audit trail to allow efficient responses to chargebacks and attempted fraud
6. It is a non goal to support payments for non-virtual goods.  The legal requirements involved in the purchase (and shipping) of goods are significantly different.

For Mozilla, we have the additional requirements of:
----------------------------------------------------

1. Mozilla-operated servers do not persist payment card data and payment card data does not transit a Mozilla-operated server.
2. Mozilla must assume that the client is under the control of the attacker; we do not have a secure client on which we can position keys or secrets.
3. The payment system should work in any modern browser, desktop or mobile, and should be a very smooth and easy experience on Firefox browsers.

We have an optional goal of:
----------------------------

1. The user should not be required to re-enter a PIN or password for every transaction; making a purchase should unlock payments for a short period of time.  (I think this is a nice-to-have and maybe a bad idea in some cases).

Threat Model:
=============

There are many ways an attacker could abuse an in-app payments model.  The big ones are:

1. A malicious application could make charges without a user's knowledge, or for a larger amount than the user expects
2. A malicious application could make charges and then not provide the user with the expected service or content
3. A malicious user, or network intermediary, could try to intercept payment flows from an app, to redirect funds to his own account
4. A man-in-the-browser attacker could try to drive payment activities and confirmations in order to drive payments to a target site
5. A malicious user could try to impersonate a payment API provider to fool the app into thinking a payment was completed
6. A network attacker could try to capture the user's payment card data, or the user's payment authorization, by attacking servers
7. The system could be so hard to use that nobody uses it.

System Outline
==============

One system that satisfies these requirements would look like this (it's broadly similar to the Google Payments-for-the-Web system, except for the use BrowserID, PayPal's preauth model, and PIN):

1. Mozilla and App Operator agree on a Payment Secret and a Postback URL.  The App Operator saves the secret on his server.

<pre>
    AppOperator: "Mozilla, please give me a secret.  My postback URL is http://app/postback"
    
    Mozilla: "Okay, AppOperator, your key is ABC and your secret is 123456."
</pre>

2. The user interacts with App, eventually triggering a purchase interaction

3. The App generates a Payment Request, which contains all of the information about the item being purchased: price, currency, name, human-readable description, machine-readable blob, and signs it with his Payment Secret, and encodes the whole thing as a JWT.

<pre>
	{
		iss: "ABC",
		aud: "marketplace.mozilla.org",
		typ: "mozilla/payments/pay/v1",
		exp: (now + an hour),
		iat: now,
		request:
	    {
	        price: 1.99,
	        currency: "USD",
	        name: "Elite Sparkle Pony",
	        description: "The shiniest pony of all!",
	        productdata: "ABC123_DEF456_GHI_789.XYZ"
	    }
	} (signed-with-AppOperatorSecret-HMAC256)
</pre>

4. The App directs the user's browser to a JavaScript buy method with this Payment Request, this method is imported from a JavaScript file loaded from ```https://marketplace.mozilla.org```.  The ```buy``` method would take the Payment Request object, a success callback, and a failure callback.

<pre>
    moz.buy(theRequestObject, onBuySuccess, onBuyFailure)
</pre>

5. The buy method opens a popup box (if no session with ```marketplace.mozilla.org``` is active) or a lightbox (if one is).  

The flow once we hit the lightbox/popup box is:

 1.  User authenticated to marketplace.mozilla.org?

 2.  If no, user prompted to BrowserID authenticate.  The app MAY provide an identity hint if it think it knows who the user is.  Text would be something like, "To complete your purchase of Elite Sparkle Pony, please SIGN IN to Mozilla!".  Note that if we have sign-in-to-the-browser, this step is easier, but we still need to support fast user-switch.

 3. Does this marketplace account have a preauthorized payment token?

 4. If no, user prompted to begin full-screen PayPal PreAuthz flow.  At completion of this flow, the preauth token is saved in the user database and the flow proceeds to 5.  (this can potentially be tricky if step #1 was in a popup: need to follow window.opener, and it could have been closed; do we have a way to get back on the rails?)

 5. Obtain a PIN for the user - this could be prompting every time, or using some short-lived client- or server-side scheme.

 6. Present purchase to user for confirmation, with name, description, and identifying information from Mozilla about the seller.  This can include their name, URL, contact information, and whatever reputation data we might want to include.  (Perhaps we highlight if they are a brand-new business, for example).

 7. User confirms purchase, or cancels

 8. If cancel, return flow to failure callback of buy method.

 9. Submit purchase call to PayPal with preauth token, PIN, Mozilla secrets, and payment details, including merchant account pulled from seller's developer account.

 10. If failure, return flow to failure callback of buy method

 11. If success, return flow to success callback of buy method with transaction ID

 12. ```marketplace.mozilla.org``` POSTs a confirmation message to the Postback URL for the seller.  This confirmation message contains all the payment request fields, plus a transaction ID, and is signed with the seller's Payment Secret.

<pre>
    {
    	iss: "marketplace.mozilla.org",
    	aud: "ABC",
    	typ: "mozilla/payments/pay/postback/v1",
    	iat: (now),
    	exp: (now + 1 hour),
        request: {
            price: 1.99,
            currency: "USD",
            name: "Elite Sparkle Pony",
            description: "The shiniest pony of all!",
            productdata: "ABC123_DEF456_GHI789.XYZ",
        }
        response: {
            transactionID: "123456123456123456"
        }
    } (signed-with-AppOperatorSecret-HMAC256)
</pre>


 13. Seller must respond to the postback with the transaction ID.

<pre>
    123456123456123456
</pre>

 14. The seller may proceed with confidence that the payment will probably complete.  Chargebacks will be delivered through a notification API at a much later time, and are the seller's responsibility to convey to the user.

How the outline corresponds to the threat model:
------------------------------------------------

Threat 1 is addressed by requiring the user to be present for purchase confirmation. We know the user is present because she presented her PIN, and because the interaction with marketplace was authenticated by a BrowserID assertion which verifies her email address.

Threat 2 is addressed by the Postback flow in steps 12 and 13.  By confirming the purchase, the seller provides enforcable proof that he received the payment; refusal to provide the services or content at that point is fraud.  Mozilla may need to provide proof of this step to a payment card processor for fraud investigation.

Threat 3 is addressed by using a preauthorization secret that is known only to Mozilla following the PayPal preauthorization flow.  Even if an attacker was able to man-in-the-middle the SSL connection for marketplace.mozilla.org, and fraudulently acquire a BrowserID assertion for the user, they would not have this secret.  The attacker could conceivably drive the user to PayPal for a new run through the preauthorization flow, but at that point they would be subject to PayPal's anti-fraud measures, which should detect the attack.

Threat 4 is addressed only by the PIN.  If the man-in-the-browser attacker manages to capture the PIN, they could drive all of the purchase interactions required to attack the user.  An addon that keylogs the PIN and then drives the browser could do this.

Threat 5 is addressed by the confirmation postback.  Even if the user impersonates the buy method, and spoofs a call to the success callback (and a subsequent postback), they do not have access to the Payment Secret.  The app MUST verify that the postback message is properly signed.

Threat 6 is addressed, for Mozilla, by not holding the payment card data on our servers, and by using a PIN for all preauthorization tokens.  Even if a network attacker captured the entire Mozilla user database, they would only have email addresses and preauth keys, not PINs.  This points out that PIN storage, if any, is a critical link in the security of the system.  It may not be wise to persist them at all (which would mean skipping optional goal #1) - but we have to abandon the lightbox if we don't persist the PIN, because it would then be phishable.

Threat 7 is addressed by removing unnecessary authentication steps whenever possible, and removing clicks whenever possible.  An authenticated, preauthorized user should see a lightbox with payment confirmation, present a PIN (safely, somehow!), and confirm the payment.  They should then receive new services or content within a span of a few seconds.

We MAY want to give ourselves an API hook to present PIN authentication in chrome.  That would fix the phishing risk, and would avoid the use of a popup for signed-in-to-the-browser users.

Future Goals: Support for Web Activities
========================================

The system described here assumes that the app supports only one payment API provider.  We could support more user choice by abstracting up a layer from here.  If, for example, the app called:

    navigator.apps.startActivity ( new Activity ( PAY, supportedProviderList, requestCallback, 
        successCallback, failureCallback ) )

... and the browser presented a list of PAY-providers, perhaps filtered by supportedProviderList, invoking the request callback when the user picked one.  The request callback would have to do the JWT-generation (signing with the appropriate Payment Secret for the selected provider), and then return to the browser, who would deliver the call to the payment provider and continue the flow.

Background reading:
===================
Google's In-App Payments API for the Web
http://code.google.com/apis/inapppayments/docs/index.html

iOS "Store Kit" API:
http://developer.apple.com/library/mac/#documentation/NetworkingInternet/Conceptual/StoreKitGuide/MakingaPurchase/MakingaPurchase.html

Android "In-App Billing" API:
http://developer.android.com/guide/market/billing/billing_overview.html
