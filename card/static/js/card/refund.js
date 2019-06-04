$(document).ready(function () {
    function calculate_total() {
        var total = 0;
        $("input:checkbox[name='vouchers']:checked").each(function () {
            total += parseFloat(String($(this).data('price')).replace(/,/g, ''));
        });

        $('#refund-total').text(total.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","));
    }

    $('#voucher-all').on('click', function () {
        var checkboxes = $(this).closest('form').find(':checkbox');
        checkboxes.prop('checked', $(this).is(':checked'));

        calculate_total();
    });

    $("input:checkbox[name='vouchers']").on('change', function () {
        // `voucher-all` checked if all selected
        $('#voucher-all').prop('checked',
            $("input:checkbox[name='vouchers']:checked").length === $("input:checkbox[name='vouchers']").length);

        calculate_total();
    });
});