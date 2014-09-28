$(function () {
    $(document).ready(function() {
        Highcharts.setOptions({
            global: {
                useUTC: false
            }
        });
    });
    
});

function render_graph(name, title, graph_type, init_url, live_url, update_frequency) {
	
	chart = new Highcharts.Chart({
        chart: {
            renderTo: name,
            type: graph_type,
            marginRight: 10,
            events: {
                load: function() {
                	
                	var series = this.series[0];
                	
                    if(init_url) {
                    	
                    	$.ajax({  
                      	  type: "GET",  
                      	  url: init_url, // "/reports/live_summary/live_user_engagement",  
                      	  beforeSend: function() {
                      	     //$('#loader_'+name).show();
                      	  },
                      	  complete: function(){
                      	     //$('#loader_'+name).hide();
                      	  },
                      	  data: '',  
                      	  success: function(coordinates_arr) {
                      		
                      		//alert('init_url:' + init_url);
                      		//alert('series:'+ series);
							  
							var len = coordinates_arr.length;
							//alert("Received resp:" + coordinates_arr + " l:"+coordinates_arr.length);
							  
							for(var idx=0; idx<len; idx++) {
								var xy = coordinates_arr[len-idx-1];
								//alert("xy:"+xy);
								var x0 = xy[0].split('-');
							  
							    var x = new Date(x0[0], parseInt(x0[1])-1, x0[2], x0[3], 0, 0, 0);
							    //year, month, day, hours, minutes, seconds, milliseconds)
							    var y = parseInt(xy[1]);
							    //alert("x:"+ x + " y:"+y);
							    //alert("series data:"+series['data']['x']);
							    ///series.data.push({x:x.getTime(), y:y});
								series.addPoint([x.getTime(), y], true, true);
							}
							
							setInterval(function() {
								
								$.ajax({  
			                      	  type: "GET",  
			                      	  url: live_url, // "/reports/live_summary/live_user_engagement",  
			                      	  beforeSend: function() {
			                      	     //$('#loader_'+name).show();
			                      	  },
			                      	  complete: function(){
			                      	     //$('#loader_'+name).hide();
			                      	  },
			                      	  data: '',  
			                      	  success: function(coordinates_arr) {
			                      		
			                      		//alert('init_url:' + init_url);
			                      		//alert('series:'+ series);
										  
										var len = coordinates_arr.length;
										//alert("Received resp:" + coordinates_arr + " l:"+coordinates_arr.length);
										  
										for(var idx=0; idx<len; idx++) {
											var xy = coordinates_arr[len-idx-1];
											//alert("xy:"+xy);
											var x0 = xy[0].split('-');
										  
										    var x = new Date(x0[0], parseInt(x0[1])-1, x0[2], x0[3], 0, 0, 0);
										    var y = parseInt(xy[1]);
										    
										    var nb = series.data.length;
										    var last_point = series.data[nb-1];
										    if(last_point.x==x.getTime()) {
										    	// only updating y
										    	last_point.update(y, true);
										    }
										    else {
										    	//alert("x:"+ x + " y:"+y);
										    	//	alert("series data:"+series['data']['x']);
										    	///series.data.push({x:x.getTime(), y:y});
										    	//alert('series_data:' + series.g)
										    
										    	series.addPoint([x.getTime(), y], true, true);
										    }
										}
			                      	  }  
			                      	});
	                        }, update_frequency);
							
							//alert('done');
                      	  }  
                      	});
                    }
                }
            }
        },
        title: {
            text: title //Live random data'
        },
        xAxis: {
            type: 'datetime',
            tickPixelInterval: 50
        },
        yAxis: {
            title: {
                text: 'Count'
            },
            plotLines: [{
                value: 0,
                width: 1,
                color: '#808080'
            }]
        },
        tooltip: {
            formatter: function() {
                    return '<b>'+ this.series.name +'</b><br/>'+
                    //Highcharts.dateFormat('%Y-%m-%d %H:%M:%S', this.x) +'<br/>'+
                    Highcharts.dateFormat('%Y-%m-%d %H:%M:%S', this.x) +'<br/>'+
                    Highcharts.numberFormat(this.y, 0);
            }
        },
        legend: {
            enabled: false
        },
        exporting: {
            enabled: false
        },
        series: [{
            name: 'Nb Registered Users',
            data: (function() {
                // generate an array of random data
                var data = []
                var nb_hours = 48;
                time = (new Date()).getTime() - nb_hours*3600*1000;
                for (i = 0; i < nb_hours; i++) {
                    data.push({
                        x: time + i*3600*1000,
                        y: 0//Math.random()
                    });
                }
                
                return data;
            })()
        }]
    });
	return chart;
}

