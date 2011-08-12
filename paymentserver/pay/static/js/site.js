function log() {
  if (typeof console != 'undefined' && console.log) {
    console.log.apply(console, arguments);
  }
}

function createErrorDiv(message) {
  var node = document.createElement('div');
  node.className = 'error';
  node.appendChild(document.createTextNode(message));
  return node;
}

window.addEventListener('load', function () {
  $("#signinlink").click(function() {
    navigator.id.getVerifiedEmail(function(assertion) {
      $("#loginassertion").val(assertion);
      $("#loginform").submit();
    })
  });
}, false);