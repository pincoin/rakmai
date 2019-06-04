(function ($) {
    $(document).ready(function () {
        $('#id_list_price').bind('keyup change', function (e) {
            $('#id_discount_rate').val(100 - 100 * $('#id_selling_price').val() / $(this).val());
        });

        $('#id_selling_price').bind('keyup change', function (e) {
            $('#id_discount_rate').val(100 - 100 * $(this).val() / $('#id_list_price').val());
        });

        $('#id_discount_rate').bind('keyup change', function (e) {
            $('#id_selling_price').val($('#id_list_price').val() * (100 - $(this).val()) / 100);
        });
    });
})(django.jQuery);