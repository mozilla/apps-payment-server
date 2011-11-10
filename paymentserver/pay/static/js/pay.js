/*
prototype of window.mozPay(...)

This would be implemented in the WebRT
*/
window.mozPay = function(signedRequest, onPaySuccess, onPayFailure, options) {
    var defaults = {clickTarget: null};
    options = $.extend(defaults, options || {});
    $(options.clickTarget).popover({
        header: '#pay-dialog > .p-header',
        content: '#pay-dialog > .p-content',
        processPayment: function(closeModal) {
            console.log(signedRequest);
            // onPaySuccess();
            closeModal();
        }
    });
    $(options.clickTarget).trigger('openpaydialog');
};
