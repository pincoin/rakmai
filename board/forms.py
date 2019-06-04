import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout, Fieldset, ButtonHolder, Submit
)
from django import forms
from django.utils.translation import gettext_lazy as _
from mptt.forms import TreeNodeChoiceField

from rakmai import settings as rakmai_settings
from . import settings as board_settings
from .models import Message
from .widgets import MessageSummernoteBs4Widget


class MessageSearchForm(forms.Form):
    TITLE = 'title'
    CONTENT = 'content'
    TITLE_CONTENT = 'title_content'
    NICKNAME = 'nickname'

    where = forms.ChoiceField(
        label=_('Search Fields'),
        widget=forms.Select(
            attrs={
                'class': 'form-control input-group mr-sm-2',
                'required': True,
            }
        ),
        choices=([
            (TITLE, _('Title')),
            (CONTENT, _('Content')),
            (TITLE_CONTENT, _('Title+Content')),
            (NICKNAME, _('Nickname')),
        ]),
        initial=TITLE_CONTENT,
        required=True,
    )

    q = forms.CharField(
        label=_('Search'),
        widget=forms.TextInput(
            attrs={
                'class': 'form-control input-group mr-sm-2',
                'placeholder': _('Search'),
                'required': 'True',
            }
        )
    )


class MessageForm(forms.ModelForm):
    category = TreeNodeChoiceField(None)  # queryset is resolved when instantiated.

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)

        # important to "pop" added kwarg before call to parent's constructor
        self.request = kwargs.pop('request', None)
        self.categories = kwargs.pop('categories', None)

        super(MessageForm, self).__init__(*args, **kwargs)

        self.fields['category'].queryset = self.categories

        # Remove trivial labels and help texts not all labels (self.helper.form_show_labels = False)
        # `self.fields` are available after calling `__init__`.
        for field_name in ['title', 'content', 'category']:
            field = self.fields.get(field_name)
            field.widget.attrs['placeholder'] = field.label
            field.label = False
            field.help_text = False

        self.helper = FormHelper()
        self.helper.include_media = False
        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                'category',
                'title',
                'content',
                'secret',
                'sticky',
            ),
            ButtonHolder(
                Submit('submit', _('Write'), css_class='btn btn-info')
            )
        )

    class Meta:
        model = Message
        fields = ['title', 'content', 'category', 'secret', 'sticky']
        widgets = {
            'content': MessageSummernoteBs4Widget(
                options={
                    'upload_url': board_settings.BOARD_FILE_UPLOAD_URL,
                    'delete_url': board_settings.BOARD_FILE_DELETE_URL,
                    'max_upload_size': rakmai_settings.UPLOAD_FILE_MAX_SIZE,
                    'content_types': rakmai_settings.UPLOAD_FILE_CONTENT_TYPES,
                    'file_extensions': rakmai_settings.UPLOAD_FILE_EXTENSIONS,
                }
            ),
        }

    def clean(self):
        # TODO: check if has permissions
        self.logger.debug(self.cleaned_data['sticky'])
        self.logger.debug(self.cleaned_data['secret'])


class MessageAttachmentForm(MessageForm):
    attachments = forms.UUIDField(widget=forms.HiddenInput(), required=False)

    def clean_attachments(self):
        data = self.data.getlist('attachments')

        count = self.instance.attachments.count() if self.instance else 0

        if count + len(data) > board_settings.MESSAGE_MAX_FILE_COUNT:
            raise forms.ValidationError(_('Maximum number of files exceeded.'))

        return data


class MessageAdminForm(forms.ModelForm):
    class Meta:
        model = Message
        # Admin sets `board`, `owner`.
        fields = (
            'board', 'category', 'sticky', 'secret', 'title', 'content', 'markup', 'status', 'is_removed',
            'owner', 'nickname',
        )
