from rakmai.widgets import SummernoteBs4Widget


class PostSummernoteBs4Widget(SummernoteBs4Widget):
    class Media:
        js = (
            'js/blog/post-summernote-ajax.js',
        )
