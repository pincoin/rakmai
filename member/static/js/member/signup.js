$(document).ready(function () {
    var last_name;
    var first_name;

    $('#id_last_name, #id_first_name').bind('keyup change', function (e) {
        last_name = $('#id_last_name').val().replace(/^\s+|\s+$/gm,'');
        first_name = $('#id_first_name').val().replace(/^\s+|\s+$/gm,'');

        var last_name_match = last_name.match(/[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]/g);
        var first_name_match = first_name.match(/[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]/g);

        if (last_name && last_name_match
            && last_name === last_name_match.join('')
            && first_name
            && first_name_match
            && first_name === first_name_match.join('')) {
            $('#valid-name-message').removeClass('d-none').addClass('d-block').text(last_name + first_name);
            $('#valid-name-message1').text('휴대폰 명의와 일치합니다.');
        } else {
            $('#valid-name-message').removeClass('d-none').addClass('d-block').text(first_name + " " + last_name);
            $('#valid-name-message1').text('외국인입니다.');
        }
    });
});