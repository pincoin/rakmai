(function ($) {
    $(document).on('formset:added', function (event, $row, formsetName) {
        if (formsetName === 'author_set') {
            console.log('added');
        }
    });

    $(document).on('formset:removed', function (event, $row, formsetName) {
        // Row removed
        console.log('removed');
    });
})(django.jQuery);