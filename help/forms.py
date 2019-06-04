from crispy_forms.helper import (
    FormHelper, Layout
)
from crispy_forms.layout import (
    HTML, Fieldset, Submit
)
from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from shop import models


class FaqMessageAdminForm(forms.ModelForm):
    class Meta:
        model = models.FaqMessage
        fields = ('category', 'title', 'content', 'store', 'position')


class NoticeMessageAdminForm(forms.ModelForm):
    class Meta:
        model = models.NoticeMessage
        fields = ('category', 'title', 'content', 'store')


class CustomerQuestionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.store_code = kwargs.pop('store_code', 'default')
        self.page = kwargs.pop('page', 1)

        super(CustomerQuestionForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.include_media = False

        self.helper.form_class = 'form'

        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                'category',
                'title',
                'content',
            ),
            HTML('''
            <button type="submit" class="btn btn-block btn-lg btn-primary my-2">
                <i class="fas fa-pencil-alt"></i> {}
            </button>
            <hr>
            <a href="{}?page={}" class="btn btn-block btn-lg btn-outline-secondary my-2">
                <i class="fas fa-list"></i> {}
            </a>
            '''.format(_('Write'), reverse('help:question-list', args=(self.store_code,)), self.page, _('List'))),
        )

    class Meta:
        model = models.CustomerQuestion
        fields = (
            'category', 'title', 'content',  # 'owner', 'store'
        )


class TestimonialsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.store_code = kwargs.pop('store_code', 'default')
        self.page = kwargs.pop('page', 1)

        super(TestimonialsForm, self).__init__(*args, **kwargs)

        self.fields['title'].help_text = False

        self.helper = FormHelper()
        self.helper.include_media = False

        self.helper.form_class = 'form'

        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                'title',
                'content',
            ),
            HTML('''
            <button type="submit" class="btn btn-block btn-lg btn-primary my-2">
                <i class="fas fa-pencil-alt"></i> {}
            </button>
            <hr>
            <a href="{}?page={}" class="btn btn-block btn-lg btn-outline-secondary my-2">
                <i class="fas fa-list"></i> {}
            </a>
            '''.format(_('Write'), reverse('help:testimonials-list', args=(self.store_code,)), self.page, _('List'))),
        )

    class Meta:
        model = models.Testimonials
        fields = (
            'title', 'content',  # 'owner', 'store'
        )


class TestimonialsAnswerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.store_code = kwargs.pop('store_code', 'default')
        self.testimonial = kwargs.pop('testimonial', 0)

        super(TestimonialsAnswerForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_action = reverse('help:testimonials-answer', args=(self.store_code, self.testimonial))
        self.helper.add_input(Submit('submit', _('Post Answer'), css_class='btn btn-lg btn-block btn-primary'))
        self.helper.form_method = 'POST'

    class Meta:
        model = models.TestimonialsAnswer
        fields = ['content']
