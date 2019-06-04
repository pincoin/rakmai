/*
function setCookie(name, value, expiredays) {
    var today = new Date();
    today.setDate(today.getDate() + expiredays);
    document.cookie = name + '=' + escape(value) + '; path=/; expires=' + today.toGMTString() + ';'
}

function getCookie(name) {
    var cName = name + "=";
    var x = 0;

    while (x <= document.cookie.length) {
        var y = (x + cName.length);
        if (document.cookie.substring(x, y) === cName) {
            if ((endOfCookie = document.cookie.indexOf(";", y)) === -1)
                endOfCookie = document.cookie.length;
            return unescape(document.cookie.substring(y, endOfCookie));
        }
        x = document.cookie.indexOf(" ", x) + 1;
        if (x === 0)
            break;
    }
    return "";
}
*/

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

    $('#language-selector').on('change', function (e) {
        this.form.submit();
    });

    $('#currency-selector').on('change', function (e) {
        this.form.submit();
    });

    /*
    var welcomeModal = $('#welcomeModal');

    if (getCookie("notToday") !== "Y") {
        welcomeModal.modal({
            keyboard: false
        });
    }

    welcomeModal.on("hidden.bs.modal", function () {
        setCookie('notToday', 'Y', 1);
    });
    */
});

$(window).on('load resize', function () {
    if ($(this).width() < 992) {
        var h = $(window).height();

        // 38x8=304
        $('.submenu-scroll').css({'max-height': h - 304, 'min-height': h - 304, 'background-color': '#fff'});
    }
});