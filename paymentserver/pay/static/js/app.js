$(function() {
    "use strict";
    var signedRequest = {}, // todo on server
        onPaySuccess,
        onPayFailure;

    function onPaySuccess() {
    }

    function onPayFailure() {
    }

    $('.products button').click(function(evt) {
        window.mozPay(signedRequest, onPaySuccess, onPayFailure,
                      {clickTarget: evt.currentTarget});
    });
});
