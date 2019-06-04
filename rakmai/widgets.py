import json

from django.forms import widgets
from django.template import loader
from django.utils.safestring import mark_safe


class SummernoteWidgetBase(widgets.Textarea):
    template_name = 'summernote/summernote.html'

    def __init__(self, attrs=None, wrapper_class='', options={}):
        self.wrapper_class = wrapper_class
        self.options = options

        super(SummernoteWidgetBase, self).__init__(attrs=attrs)

    def render(self, name, value, attrs=None, renderer=None):
        context = {
            'widget': {
                'name': name,
                'value': value,
                'wrapper_class': self.wrapper_class,
                'options': json.dumps(self.options),
            }
        }

        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)


class SummernoteLiteWidget(SummernoteWidgetBase):
    class Media:
        css = {
            'all': (
                'css/summernote/summernote-lite.css',
            )
        }
        js = (
            'js/rakmai/csrf-cookie.js',
            'js/summernote/summernote-lite.js',
        )


class SummernoteBs3Widget(SummernoteWidgetBase):
    class Media:
        css = {
            'all': (
                'css/summernote/summernote.css',
            )
        }
        js = (
            'js/rakmai/csrf-cookie.js',
            'js/summernote/summernote.min.js',
        )


class SummernoteBs4Widget(SummernoteWidgetBase):
    class Media:
        css = {
            'all': (
                '//cdnjs.cloudflare.com/ajax/libs/codemirror/3.20.0/codemirror.css',
                'css/summernote/summernote-bs4.css',
            )
        }
        js = (
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/3.20.0/codemirror.js',
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/3.20.0/mode/xml/xml.js',
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/2.36.0/formatting.js',
            'js/rakmai/csrf-cookie.js',
            'js/summernote/summernote-bs4.min.js',
        )


class SimplemdeWidget(widgets.Textarea):
    template_name = 'simplemde/simplemde.html'

    def __init__(self, attrs=None, wrapper_class='', options={}):
        self.wrapper_class = wrapper_class
        self.options = options

        super(SimplemdeWidget, self).__init__(attrs=attrs)

    def render(self, name, value, attrs=None, renderer=None):
        context = {
            'widget': {
                'name': name,
                'value': value,
                'wrapper_class': self.wrapper_class,
                'options': json.dumps(self.options),
            }
        }

        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)

    class Media:
        css = {
            'all': (
                'css/simplemde/simplemde.min.css',
            )
        }
        js = (
            'js/rakmai/csrf-cookie.js',
            'js/simplemde/simplemde.min.js',
        )
