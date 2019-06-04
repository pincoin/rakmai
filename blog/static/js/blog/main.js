$(document).ready(function () {
    var navbar = $('#navbarsTop');
    var toggler = $('#navbar-toggle-button');
    var grayLayer = $('.gray-layer');
    var body = $('body');

    toggler.click(function (e) {
        navbar.toggleClass('left-sidebar');
        navbar.css('z-index', 1040);
        toggler.toggleClass('indexcity');
        navbar.collapse('toggle');
        grayLayer.toggle();
        body.toggleClass('scroll-lock');

        /* scroll-lock */
        grayLayer.on('scroll touchmove mousewheel', function (e) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        });

        e.stopPropagation();
    });

    grayLayer.on('click', function (e) {
        // for small devices
        if ($(window).width() <= 768 && navbar.is(":visible") && e.target.id !== 'navbarsTop' && e.target.id !== 'id_q') {
            $("button.navbar-toggler").click();
        }
    });

    var before_send = function (xhr, settings) {
        if ('beforeSend' in $.ajaxSettings) {
            // Set CSRF token by calling default `beforeSend`.
            $.ajaxSettings.beforeSend(xhr, settings);
        }
    };

    $(document).on('click', '.close', function (e) {
        // data-dismiss completely removes the element.
        // Use jQuery's .hide() method instead.
        $('.cart-alert').hide();
    });
});