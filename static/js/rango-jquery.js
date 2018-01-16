$(document).ready( function() { 
    $("#about-btn").click( function(event) {
        msgstr = $("#msg").html()
        msgstr = msgstr + "ooo"
        $("#msg").html(msgstr)
    });

    $(".hehe").click(function(event) {
        alert("Thai che...thai che click");
    });

    $("p").hover( function() { 
        $(this).css('color', 'red');
    }, 
    function() {
        $(this).css('color', 'blue'); 
    })
});