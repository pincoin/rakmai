from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout, Fieldset, Div, Submit, HTML
)
from django import forms
from django.utils.translation import ugettext_lazy as _
from mptt.forms import TreeNodeChoiceField

from rakmai import settings as rakmai_settings
from . import settings as book_settings
from .models import (
    Book, Page, Attachment
)
from .widgets import PageSimplemdeWidget


class BookForm(forms.ModelForm):
    category = TreeNodeChoiceField(None)

    def __init__(self, *args, **kwargs):
        self.categories = kwargs.pop('categories', None)

        super(BookForm, self).__init__(*args, **kwargs)

        self.fields['category'].queryset = self.categories
        self.fields['category'].required = False
        self.fields['category'].label = _('category')

        self.helper = FormHelper()
        self.helper.include_media = False

        # horizontal grid form
        self.helper.form_class = 'form-horizontal'  # Appends `row` class to `div` surrounding label and form field
        self.helper.label_class = 'col-2 col-form-label'
        self.helper.field_class = 'col-10'

        # `category` field is selectively hidden.
        fieldset = [
            '',  # Hide the legend of fieldset (HTML tag)
            'title',
            'description',
        ]

        if self.categories:
            fieldset.append('category')
            self.fields['category'].required = True

        fieldset += [
            'thumbnail',
            'status',
            'license',
        ]

        self.helper.layout = Layout(
            Fieldset(*fieldset),
            Div(
                Submit('submit', _('Write'), css_class='btn btn-info'),
                css_class='offset-md-2 col-md-10 submit-padding-left',
            )
        )

    class Meta:
        model = Book
        fields = ('title', 'description', 'category', 'thumbnail', 'status', 'license')
        widgets = {
            'description': PageSimplemdeWidget(),
        }


class BookAdminForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = (
            'title', 'description', 'category', 'thumbnail', 'status', 'license', 'owner'
        )


class PageForm(forms.ModelForm):
    parent = TreeNodeChoiceField(None)

    def __init__(self, *args, **kwargs):
        self.categories = kwargs.pop('parents', None)

        super(PageForm, self).__init__(*args, **kwargs)

        # Note: Retrieves self.instance when update after __init__
        self.attachments = Attachment.objects.filter(page__id=self.instance.id) if self.instance.id else []

        self.fields['parent'].queryset = self.categories
        self.fields['parent'].required = False
        self.fields['parent'].label = _('parent')

        self.helper = FormHelper()
        self.helper.include_media = False

        # horizontal grid form
        self.helper.form_class = 'form-horizontal'  # Appends `row` class to `div` surrounding label and form field
        self.helper.label_class = 'col-2 col-form-label'
        self.helper.field_class = 'col-10'

        thumbnail = []

        # Constructs thumbnail list for edit
        for attachment in self.attachments:
            s = '''
                    <div id="thumbnail-card-{0}" class="col-lg-3 col-md-3 col-sm-4 mt-2">
                        <div class="card h-100">
                            <div class="card-body">
                                <img class="card-img-top page-thumbnail-image" src="{1}" width="118" height="68">
                            </div>
                            <div class="card-footer text-center">
                                <a href="#" class="btn-sm btn-danger page-thumbnail-delete-button" id="thumbnail-{0}">Delete</a>
                            </div>
                        </div>
                    </div>
                    '''.format(attachment.uid, attachment.file.url)

            thumbnail.append(s)

        thumbnail_section = ''.join(thumbnail)

        # `category` field is selectively hidden.
        fieldset = [
            '',  # Hide the legend of fieldset (HTML tag)
            'title',
            'parent',
            'content',
            HTML('''
                        <div class="row mb-4">
                            <div class="col-2"></div>
                            <div class="col-10"><div id="thumbnail-list" class="row">{0}</div></div>
                        </div>
                    '''.format(thumbnail_section)),
            'status',
            'keywords',
            'description',
        ]

        self.helper.layout = Layout(
            Fieldset(*fieldset),
            Div(
                Submit('submit', _('Write'), css_class='btn btn-info'),
                css_class='offset-md-2 col-md-10 submit-padding-left',
            )
        )

    class Meta:
        model = Page
        fields = ('title', 'content', 'keywords', 'description', 'parent', 'status')
        widgets = {
            'content': PageSimplemdeWidget(
                options={
                    'upload_url': book_settings.BOOK_FILE_UPLOAD_URL,
                    'delete_url': book_settings.BOOK_FILE_DELETE_URL,
                    'max_upload_size': rakmai_settings.UPLOAD_FILE_MAX_SIZE,
                    'content_types': rakmai_settings.UPLOAD_FILE_CONTENT_TYPES,
                    'file_extensions': rakmai_settings.UPLOAD_FILE_EXTENSIONS,
                }
            ),
        }


class PageAttachmentForm(PageForm):
    attachments = forms.UUIDField(widget=forms.HiddenInput(), required=False)

    def clean_attachments(self):
        data = self.data.getlist('attachments')

        count = self.instance.attachments.count() if self.instance else 0

        if count + len(data) > book_settings.PAGE_MAX_FILE_COUNT:
            raise forms.ValidationError(_('Maximum number of files exceeded.'))

        return data


class PageSearchForm(forms.Form):
    q = forms.CharField(
        label=_('search word'),
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('search word'),
                'required': 'True',
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        q = kwargs.pop('q', '')

        super(PageSearchForm, self).__init__(*args, **kwargs)

        self.fields['q'].initial = q
