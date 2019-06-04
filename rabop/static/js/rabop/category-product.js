$(document).ready(function () {
    $.getJSON('/shop/product.json', function (data) {
        var vouchers = data['context'];

        for (var i = 0; i < vouchers.length; i++) {
            $('#id_stock').append('<option value="' + i + '">' + vouchers[i].title + '</option>');
        }

        $(document).on('change', '#id_stock', function (e) {
            if ($(this).val() > -1) {
                var voucher = vouchers[$(this).val()];
                var amount_options = $('#id_product');

                amount_options.empty();

                for (var i = 0; i < voucher.amount.length; i++) {
                    if (i === 0) {
                        amount_options.append('<option value="' + voucher.amount[i].pk + '" selected>' + voucher.amount[i].title + '</option>');
                    } else {
                        amount_options.append('<option value="' + voucher.amount[i].pk + '">' + voucher.amount[i].title + '</option>');
                    }
                }
            }
        });
    });
});