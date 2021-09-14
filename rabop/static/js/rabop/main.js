$(document).ready(function () {
    var navbar = $('#navbarsTop');
    var toggler = $('#navbar-toggle-button');

    toggler.click(function (e) {
        navbar.toggleClass('left-sidebar');
        toggler.toggleClass('indexcity');
        navbar.collapse('toggle');
        e.stopPropagation();
    });

    $(document).on('click', function (e) {
        if (navbar.is(":visible") && e.target.id !== 'id_q') {
            $("button.navbar-toggler").click();
        }
    });

    $('#id_status').on('change', function (e) {
        this.form.submit();
    });

    $('#id_voucher').on('change', function (e) {
        this.form.submit();
    });

    $('#id_order_by').on('change', function (e) {
        this.form.submit();
    });

    var messages = [
        '발송지연으로 불편을 드려 대단히 죄송합니다.\n\n',
        '발권 처리해드렸습니다. 주문/발송 내역 페이지에서 확인 부탁드립니다.\n\n감사합니다.\n\n',
        '주문자/입금자 이름이 다를 경우 무조건 다음 날 수수료 500원을 제외한 금액 환불 입금 처리됩니다.\n\n입금자 명의 환불 받으실 은행 이름과 계좌번호를 문의하기에 남겨주세요.\n\n감사합니다.',
        '교환 또는 환불은 미사용에 한하여 요청일로부터 은행영업일 기준 3~5일 이후 환불 수수료 500원 제외하고 입금됩니다.\n\n감사합니다.\n\n',
        '수수료 500원을 제외한 금액 원 환불 입금 처리되었습니다.\n\n확인 부탁드립니다. 감사합니다.\n\n',
        'unverified 페이팔 계정은 무조건 주문무효 및 환불처리됩니다.\n\n반드시 페이팔에 로그인해서 get verified 메뉴에서 결제수단인증 완료 후 주문결제 해주세요.\n\n감사합니다.\n\n',
        '카드 결제로 상품권을 구매할 수 없는 카드이거나 할부로 진행한 경우입니다.\n\n최종 결제승인되지 않았으므로 카드사 홈페이지에서 결제승인내역 확인바랍니다.\n\n감사합니다.\n\n',
        '다음에 주문/입금하실 때 차액 빼고 입금해주세요.\n\n단, 이 경우 수동발권처리해야 하므로 오전10시부터 밤11시 사이에 주문/입금부탁드립니다.\n\n' +
        '또는 환불 수수료 500원을 제외한 금액 환불 받으실 은행 이름, 계좌번호, 입금주를 고객문의에 남겨주세요. 다음 날 처리됩니다.\n\n감사합니다.\n\n',
        '컬쳐랜드 발행 온라인 문화상품권은 크게 두 종류가 있습니다.\n\n' +
        '컬쳐랜드 PIN 1234-1234-1234-123456 (총 18자리)\n' +
        '모바일 문화상품권 1234-1234-1234-1234 (총 12자리)\n\n' +
        '따라서 12자리  모바일 문화상품권을 받으신 경우에는\n\n' +
        '컬쳐랜드에서 모바일문화상품권으로 선택하여 충전 후 아이디로 결제 진행 부탁드립니다.\n\n감사합니다.\n\n',
        '처리해드렸습니다. 감사합니다.\n\n',
        '내일 중으로 처리됩니다. 감사합니다.\n\n',
        '감사합니다.\n\n'
    ];

    $('#id_answer').on('change', function (e) {
        if (this.value > 0) {
            var key = this.value - 1;

            $('#id_content').val(function (i, text) {
                return text + messages[key];
            });
        }
    });

    var sms_messages = [
        '[핀코인] ',
        '[핀코인] 신분증 사진도 주민번호는 가리고 이름/생년월일/주소 일부가 보이게 올려주세요.',
        '[핀코인] 화면캡처 아닌 실물 통장 또는 카드 사진도 번호는 가리고 앞면 이름이 보이게 올려주세요.',
        '[핀코인] 입금액이 부족합니다. 차액 입금하거나 주문취소 후 입금액에 맞게 재주문해주세요.',
        '[핀코인] 주문자/입금자 이름 불일치는 무조건 환불처리되며 고객센터 문의하기에 은행이름/계좌번호 남겨주세요.',
        '[핀코인] 미사용에 한하여 환불요청일로부터 3~5일 후 수수료 500원 제외하고 입금됩니다.',
        '[핀코인] 주문 후 1시간 이내 입금하지 않으면 자동삭제됩니다. 새로 주문만 완료해주세요.'
    ];

    $('#id_sms_answer').on('change', function (e) {
        if (this.value > 0) {
            var key = this.value - 1;

            $('#id_content').val(function (i, text) {
                return text + sms_messages[key];
            });
        }
    });
});