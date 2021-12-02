
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