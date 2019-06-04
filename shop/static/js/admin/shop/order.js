(function ($) {
    $(document).ready(function () {
        $('input[name=_back]').on('click', function (e) {
            history.back();
        });
    });
})(django.jQuery);