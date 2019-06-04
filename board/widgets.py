from rakmai.widgets import (
    SummernoteBs4Widget, SummernoteLiteWidget
)


class MessageSummernoteBs4Widget(SummernoteBs4Widget):
    class Media:
        js = (
            'js/board/message-summernote-ajax.js',
        )


class MessageAdminSummernoteLiteWidget(SummernoteLiteWidget):
    class Media:
        css = {
            'all': (
                'css/django-summernote.css',
            )
        }
        js = (
            'js/post-admin-summernote-ajax.js',
        )
