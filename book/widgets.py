from rakmai.widgets import SimplemdeWidget


class PageSimplemdeWidget(SimplemdeWidget):
    class Media:
        css = {
            'all': (
                'css/book/page-simplemde.css',
            )
        }
        js = (
            'js/book/page-simplemde-ajax.js',
        )
