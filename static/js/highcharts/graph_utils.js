/*To change the chart type, e.g. line, spline, column
#TODO pass types from sever side constants e.g. LINE 
#bar etc, need to added .
*/
var graph_extremes={};
function change_chart_type(chart_id,select,chart_number){
	var chart=$("#"+chart_id).highcharts();
	chart.options.chart.type=select.value;
	new Highcharts.Chart(chart.options);
	
	// Empty Range selectore if appears 
	if ( $("#"+chart_id+"_min").val() &&  $("#"+chart_id+"_max").val()){
		change_min_max (chart_id , chart_number);
	}
	
}
function reset_extremes(chart_id,chart_number){
	
	var chart_extreme_id =chart_id+"_"+chart_number;
	if (chart_extreme_id  in graph_extremes ){
		var chart=$("#"+chart_id).highcharts();
		chart.yAxis[chart_number-1].setExtremes(graph_extremes[chart_extreme_id]["min"],graph_extremes[chart_extreme_id]["max"])
	}
	$("#"+chart_id+"_min").val("")
        $("#"+chart_id+"_max").val("")

	// Not required 
	//chart.xAxis[0]["max"]=chart.xAxis[0]["dataMax"];
	//because set values after sliding not effecting these values.
	new Highcharts.Chart(chart.options);
}
function change_min_max (chart_id , chart_number){
	var chart_extreme_id =chart_id+"_"+chart_number;
	var chart=$("#"+chart_id).highcharts();
	if (! (chart_extreme_id  in graph_extremes )){
		graph_extremes[chart_extreme_id]= chart.yAxis[chart_number-1].getExtremes()
	}

	var min= parseInt($("#"+chart_id+"_min").val());
	var max= parseInt($("#"+chart_id+"_max").val());
	if ( isNaN(min) && isNaN(max) ){
		alert("No range val selected");
		return 
	}
	if ( isNaN(min) ) {
		min=0;
	}
	if (isNaN(max)){
		alert("Please enter a max value");
		return;
	}
	
	chart.yAxis[chart_number-1].setExtremes(min,max)
}

function highstock_last_n_days(chart_id, days){	
	var chart = $("#"+chart_id).highcharts();
	if (chart.options.series.length){
		var series = chart.options.series;
		var max_date =new Date(series[0]['data']  [series[0]['data'].length -1][0]);
		var before_n_days = new Date();
		before_n_days.setDate(max_date.getDate()-days);
		max_date=max_date.getTime();
		before_n_days=before_n_days.getTime();
		chart.xAxis[0].setExtremes(before_n_days,max_date);
	}
}

jQuery.fn.ForceNumericOnly =
	function()
	{
	    return this.each(function()
	    {
	        $(this).keydown(function(e)
	        {
	            var key = e.charCode || e.keyCode || 0;
	            // allow backspace, tab, delete, enter, arrows, numbers and keypad numbers ONLY
	            // home, end, period, and numpad decimal
	            return (
	                key == 8 || 
	                key == 9 ||
	                key == 13 ||
	                key == 46 ||
	                key == 110 ||
	                key == 190 ||
	                (key >= 35 && key <= 40) ||
	                (key >= 48 && key <= 57) ||
	                (key >= 96 && key <= 105));
	        });
	    });
	};
