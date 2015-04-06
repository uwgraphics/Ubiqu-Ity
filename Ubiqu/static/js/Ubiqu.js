$('#ubiqu_upload_form').append("<input type='hidden' name='javascript_enabled' value='true'>");

$('#ubiqu_upload_form').ajaxForm({
    beforeSubmit: function(formData, jqForm, options) {
        var form = jqForm[0];
        if (!form.Text.value) {
            alert('Please choose some texts (or ZIP archive/s, or both) to upload.');
            return false;
        }
        if (!form.email_address.value) {
            alert('Please enter your email address.');
            return false;
        }
        $("#ubiqu_upload_submit, #ubiqu_upload_reset").attr("disabled", "true");
        $("#ubiqu_upload_progress").addClass("progress-striped").addClass("active");

        var $progress_message = $("<div></div>");
        // Add the date.
        $progress_message.append("<small class='date muted'>" + Date.now() + "</small><br>");
        var $message = $("<div class='message'><span class='label label-warning'>Uploaded</span> Please wait...</div>");
        $progress_message.append($message);
        $progress_message.hide();
        $("#output_content").append($progress_message);
        $progress_message.fadeIn(250);
    },
    dataType: "json",
    uploadProgress: function(event, position, total, percentComplete) {
        $("#ubiqu_upload_progress .bar").css("width", percentComplete + '%');
    },
    success: function(responseText, statusText, xhr, $form) {
        // The upload route returns a redirect to the status page.
        document.location.href = responseText.redirect;
    }
});
