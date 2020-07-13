$(document).ready(function () {
    $.getJSON('/shop/product.json', function (data) {
        var vouchers = data['context'];

        for (var i = 0; i < vouchers.length; i++) {
            $('#id_stock').append('<option value="' + i + '">' + vouchers[i].title + '</option>');
        }

        $(document).on('change', '#id_stock', function (e) {
            if ($(this).val() > -1) {
                var voucher = vouchers[$(this).val()];
                var amount_options = $('#id_amount');

                amount_options.empty();

                for (var i = 0; i < voucher.amount.length; i++) {
                    amount_options.append('<option value="' + voucher.amount[i].pk + '">' + voucher.amount[i].title + '</option>');
                }
            }
        });

        $(document).on('click', '#id_parse', function () {
            var content = $('#id_content').val();

            var voucher_idx = $('#id_stock').val();
            var voucher_product = $('#id_amount').val();
            var voucher_remarks = $('#id_remarks').val();
            var error_message1 = $('#id_error1');
            var error_message2 = $('#id_error2');

            var results = null;
            var remarks = '';

            switch (vouchers[voucher_idx].id) {
                case 2: // 구글기프트카드
                    results = content.match(/[A-Z0-9]{4}([- ]*[A-Z0-9]{4}){3,4}/mg);
                    break;
                case 10: // 에그머니
                    results = content.match(/[0-9]{5}-[0-9]{5}-[0-9]{5}-[0-9]{5}/mg);
                    break;
                case 3: // 넥슨카드
                    results = content.match(/[A-Z]{5}-[A-Z]{5}-[A-Z]{5}-[A-Z]{5}/mg);

                    if (results === null) {
                        results = content.match(/[A-Z]{20}/mg);
                    }
                    break;
                case 11: // 해피머니 (code) remarks는 별도 수동 입력
                    if (voucher_remarks.match(/[0-9]{8}/g) !== null) {
                        results = content.match(/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}/mg);
                        remarks = voucher_remarks;
                    }
                    break;
                case 8: // 문화상품권
                case 6: // 스마트문화상품권
                    results = content.match(/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4,6}/mg);

                    if (results === null) {
                        results = content.match(/[0-9]{16,18}/mg);
                    }
                    break;
                case 7: // 도서문화상품권 (code + remarks)
                    results = content.match(/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}[ \t\n-]+[0-9]{4}/mg);
                    break;
                case 22: // 아프리카 TV (code + remarks)
                    results = content.match(/[A-Z0-9]{16}[ \t\n-]+[0-9]{6}/mg);
                    break;
                case 14: // 틴캐시
                case 18: // 매니아선불쿠폰
                case 19: // 아이템베이
                    results = content.match(/[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}/mg);
                    break;
                case 13: // 온캐시
                    results = content.match(/[0-9]{5}-[0-9]{5}-[0-9]{5}-[A-Z]{5}/mg);
                    break;
                case 4: // 퍼니카드
                    results = content.match(/[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}/mg);
                    break;
                case 16: // N코인
                case 17: // 와우캐시
                    results = content.match(/[A-Z][0-9]{3}-[0-9]{4}-[0-9]{4}/mg);
                    break;
            }

            if (results != null) {
                var json = [];

                for (var i = 0; i < results.length; i++) {
                    var voucher = {};

                    if (vouchers[voucher_idx].id === 7) { // 도서문화상품권
                        voucher.code = results[i].substr(0, 19);
                        voucher.remarks = results[i].substr(-4);
                    } else if (vouchers[voucher_idx].id === 22) { // 아프리카 TV
                        voucher.code = results[i].substr(0, 16);
                        voucher.remarks = results[i].substr(-6);
                    } else {
                        voucher.code = results[i];
                        voucher.remarks = remarks;
                    }

                    json.push(voucher);
                }

                $('#id_json_content').val(JSON.stringify(json));

                $('#id_stock1').val(vouchers[voucher_idx].title);

                $('#id_amount1').val($('#id_amount option:selected').text());
                $('#id_product').val(voucher_product);

                $('#id_count').val(results.length);

                error_message1.removeClass('d-block').addClass('d-none');
                error_message2.removeClass('d-block').addClass('d-none');
            } else {
                error_message1.removeClass('d-none').addClass('d-block');
                error_message1.text('올바르지 않은 상품권 형식');
            }
        });

        $('form').on('submit', function () {
            var voucher_name = $('#id_stock1').val();
            var voucher_remarks = $('#id_remarks').val();
            var error_message2 = $('#id_error2');

            if ($('#id_stock option:selected').text() !== voucher_name || $('#id_amount option:selected').text() !== $('#id_amount1').val()) {
                error_message2.removeClass('d-none').addClass('d-block');
                error_message2.text('아직 변환 안 됨');
                return false;
            }

            if (voucher_name === '해피머니' && voucher_remarks.match(/[0-9]{8}/g) === null) {
                error_message2.removeClass('d-none').addClass('d-block');
                error_message2.text('해피머니 발행일자 없음');
                return false;
            }

            if (voucher_name !== '해피머니' && voucher_remarks !== '') {
                error_message2.removeClass('d-none').addClass('d-block');
                error_message2.text('불필요한 비고 데이터');
                return false;
            }
        });
    });
});