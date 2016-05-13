$('#ubiqu_upload_form').append("<input type='hidden' name='javascript_enabled' value='true'>");

$('#ubiqu_upload_form').ajaxForm({
    beforeSubmit: function(formData, jqForm, options) {
        var form = jqForm[0];

        if (!form.Text.value) {
            alert('Please choose some texts (or ZIP archive/s, or both) to upload.');
            return false;
        }
		if ((form.text_upload.value.indexOf('.txt') == -1) && (form.text_upload.value.indexOf('.zip') == -1)){
			alert('Invalid corpus file type. Please select a .txt file or zip archive to upload.');
			return false;
		}
        if (!form.email_address.value) {
            alert('Please enter your email address.');
            return false;
        }

        if (+form.chunk_length.value < +form.chunk_offset.value){
            alert('Chunk length must be greater than or equal to chunk offset to prevent gaps in chunks.');
            return false;
        }
		
		if (chunk_text.checked && (generate_rule.checked || doc_rule.checked)){
			alert('Text chunking and rule csv generation are not compatible at this time. Please disable one.');
			return false;
		}
		
		if ((form.rulesChoice2.checked) && (form.SimpleRuleInput.value.indexOf('.csv') == -1)){
			alert('Simple rule dictionary must be in csv format.');
			return false;
		}

		if (form.text_upload.files.length > 50){
			alert('Please limit file uploads to at most 50 files. Upload a zip folder if you would like analyze more.');
			return false;
		}
		
		var job_s = 0;
		for (var i = text_upload.files.length; i--;) {
			job_s += text_upload.files[i].size;
		}
		if (job_s > 52428800){
			alert('The job size for the web version of Ubiq+Ity is limited to 50mb.');
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

$('#chunk_text').change(function(){
    $('#chunk_params').toggle(this.checked);
});

$('#enable_blacklist').change(function(){
    $('#blacklist_params').toggle(this.checked);
});

$('#generate_ngram_csv').change(function(){
    $('#ngram_params').toggle(this.checked);
});

$('#generate_rule').change(function(){
    $('#rule_params').toggle(this.checked);
});



