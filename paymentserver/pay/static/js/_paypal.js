$(function() {
  var goForm = function() {
  	try {
  	$.ajax({
  		url: "/init_embedded_payment", 
  		type: "POST",
  		data: {
  			csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
  			sender: $("#setup_sender").val(),
  			receiver: $("#setup_receiver").val(),
  			amount: $("#setup_amount").val(),
  			cc: $("#setup_currency").val()
  		},
  		/*dataType: "json",*/
  		success: function(data, textStatus, jqXHR) {
  			$("#ppal_paykey").val(data.paykey);
  			if (data.preapprovalKey) {
  				$("#ppal_preapprovalkey").val(data.preapprovalKey);
  			}
  			$("#ppal_form").show();
  			//$("#ppal_form").submit();
  		}, 
  		error: function(jqXHR, textStatus, errorThrown) {
        console.log("failure");
  			console.log(textStatus);
  		}
  	});
  	} catch (e) {alert(e);}
  };
  $("#setup_form_submit").live('submit', function(evt) {
    evt.preventDefault();
    goForm();
  });
});
