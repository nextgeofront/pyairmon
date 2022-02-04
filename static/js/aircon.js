
$(document).ready(function(){

    $(function(_data){
        var _data = {
            labels: [ 'JAN', 'FEB', 'MAR', 'APR',
                'MAY', 'JUN', 'JUL', 'AUG',
                'SEP', 'OCT', 'NOV', 'DEC'],
            datasets: [{
                fillColor: "rgba(151,187,205,0.2)",
                strokeColor: "rgba(151,187,205,1)",
                pointColor: "rgba(151,187,205,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(151,187,205,1)",
                bezierCurve : false,
                data: [
                    ,,,,10, 13, 14, 15,
                ]
            }],
            options: {
                responsive: false,
                maintainAspectRatio: false,
            }
        }

        $.ajax({
            url: '/thermometer',
            type: 'GET',
            success: function(data) {
                if(data.result.code == 0) {
                        _data.labels = [];
                        _data.datasets[0].data = []
                        data.datas.forEach(function (d, index) {
                            if (index > 9) {
                                return ;
                            }
                            var temp = new String(d.upload_time) ;
                            _data.labels.push( temp.substring(8,10) + ":" + temp.substring(10,12))
                            _data.datasets[0].data.push(d.temperature)
                        });
                };

                steps = 10
                var mychart = document.getElementById("chart").getContext("2d");
                new Chart(mychart).Line(_data, {
                    scaleOverride: true,
                    scaleSteps: steps,
                    scaleStepWidth: Math.ceil(30 / steps),
                    scaleStartValue: 5,
                    scaleShowVerticalLines: true,
                    scaleShowGridLines : true,
                    barShowStroke : true,
                    scaleShowLabels: true,
                    bezierCurve: false,
                });
            },
            error: function(error) {
                console.log(error);
            }
        }) ;





    });


}) ;

fn_button_on = $(function(){
   $('#button_on').click(function(){
       $.ajax({
           url: '/aircon_on',
           type: 'GET',
           success: function(response) {
               console.log(response);
               location.reload();
           },
           error: function(error) {
               console.log(error);
           }
       });
   })
});

fn_button_off = $(function(){
    $('#button_off').click(function(){
        $.ajax({
            url: '/aircon_off',
            type: 'GET',
            success: function(response) {
                console.log(response);
                location.reload();
            },
            error: function(error) {
                console.log(error);
            }
        });
    })
});
