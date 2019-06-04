$(document).ready(function () {
    $('#button-phone-verification').on('click', function () {
        window.open("", "auth_popup", "width=430,height=590,scrollbar=yes");

        var form1 = document.form1;
        form1.target = "auth_popup";
        form1.submit();
    });
});