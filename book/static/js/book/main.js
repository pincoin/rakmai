$(document).ready(function () {
    var display = false;

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

    $(window).on('scroll', function () {
        if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
            $('#topButton').css('display', 'block');
        } else {
            $('#topButton').css('display', 'none');
        }
    });

    $('#topButton').on('click', function () {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
        $('#side-table-of-contents').css('display', 'block');
    });

    $('#toc-toggle-button').on('click', function (e) {
        $('#side-table-of-contents').toggle('fast');
    });

    $('.page-content a').not($('.page-content .toc a')).attr('target', '_blank');

    /*
    document.getElementById('toc-toggle-button').addEventListener('click', function () {
        var toc = document.getElementById('side-table-of-contents');
        toc.style.display = (toc.style.display === 'none') ? 'block' : 'none';
    });
    */
});