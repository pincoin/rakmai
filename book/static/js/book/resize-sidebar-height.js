$(window).on('load resize', function () {
    if ($(this).width() >= 992) {
        $('.list-scrollable').css('max-height', $('.page').height());
    } else {
        $('.list-scrollable').css('max-height', '');
    }
});