function export_to_csv(src_obj, table_obj, csv_filename) {

    var src_obj_html = src_obj.html();
    src_obj.html("");

    var data = null;

    table_obj.children().each(function() {
	var kid = $(this);
	kid.children().each(function() {
	    row = $(this);

	    var line = null;
	    row.children().each(function () {
		field_val = $.trim($('.field_val',this).html());
		//surround in quotes if has whitespace
		if(/\s/g.test(field_val)) {
		    field_val = '"' + field_val + '"';
		}
		else {
		    //all one word, kill number formatting characters
		    field_val = field_val.replace(/[\,\$%]/g,'');
		}
        field_val = field_val.replace(/\s{2,}/g,' ');
		if(line==null) {
		    line = field_val;
		}
		else {
		    line = line + "," + field_val;
		}
	    });

	    if(line) {
		if(!data) {
		    data = line;
		}
		else {
		    data = data + "\n" + line;
		}
	    }
	});
    });
    //alert("DATA:"+data);

    if(csv_filename && csv_filename.length>0) {
        table_title = csv_filename;
    }
    else {
        table_title = $.trim(table_obj.children().children().children().children().html() );
        if(table_title=="") {
	        table_title = "report";
        }
    }

    src_obj.html(src_obj_html);

    $("#tmp_form_name").attr('value', table_title);
    $("#tmp_form_data").attr('value', data);

    $("#export_form").submit();

    $("#tmp_form_name").attr('value', '');
    $("#tmp_form_data").attr('value', '')

    return true;
}
