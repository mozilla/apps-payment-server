$(function() {
  "use strict";

  // todo: hack apart the plugin so we can do:
  // $('.products button').click(function() { window.mozPay(...); });
  $('.products button').popover({
      header: '#pay-dialog > .p-header',
      content: '#pay-dialog > .p-content'
  });
});
