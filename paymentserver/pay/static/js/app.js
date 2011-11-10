$(function() {
    "use strict";
    var onPaySuccess,
        onPayFailure;

    function onPaySuccess() {
    }

    function onPayFailure() {
    }

    $('.products button').click(function(evt) {
        var signedRequest = $(evt.currentTarget).attr('data-request');
        window.mozPay(signedRequest, onPaySuccess, onPayFailure,
                      {clickTarget: evt.currentTarget});
    });
});
