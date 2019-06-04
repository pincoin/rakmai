$(document).ready(function () {
    $('#book-page-content img').each(function () {
        var image = $(this);

        image.addClass('img-fluid rounded border border-dark mx-auto d-block');
        image.wrap($("<a>").attr({
            'data-target': '#lightboxModal',
            'data-toggle': 'modal',
            'data-src': image.attr('src'),
            'title': '이미지를 확대해서 보려면 클릭하세요.'
        }));
    });

    $('#lightboxModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var src = button.data('src');
        var modal = $(this);

        modal.find('.modal-body img').attr('src', src);

        modal.find('.modal-body').css({
            'display': 'block',
            'overflow': 'auto'
        });
    });
});