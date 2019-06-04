$(document).ready(function () {
    $('#button-id-submit').on('click', function () {
        var form = $('form[id=comment-form]');

        $.ajax({
            type: 'post',
            url: form.attr('action'),
            data: form.serialize(),
            dataType: 'json',
            cache: false,
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        }).done(function (data, textStatus, jqXHR) {
            console.log(data);

            form[0].reset();
            // $('#comment-form-div').css('display', 'none');
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.log(errorThrown);
        });
    });
});