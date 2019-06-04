from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout, Fieldset, Submit, HTML, Div
)
from django import forms
from django.utils.translation import ugettext_lazy as _
from mptt.forms import TreeNodeChoiceField

from rakmai import settings as rakmai_settings
from . import settings as blog_settings
from .models import (
    Post, Attachment
)
from .widgets import PostSummernoteBs4Widget


class PostForm(forms.ModelForm):
    category = TreeNodeChoiceField(None)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.categories = kwargs.pop('categories', None)

        super(PostForm, self).__init__(*args, **kwargs)

        # Note: Retrieves self.instance when update after __init__
        self.attachments = Attachment.objects.filter(post__id=self.instance.id) if self.instance.id else []

        self.fields['category'].queryset = self.categories
        self.fields['category'].required = False
        self.fields['category'].label = _('category')
        self.fields['title'].help_text = False

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
                        <img class="card-img-top post-thumbnail-image" src="{1}" width="118" height="68">
                    </div>
                    <div class="card-footer text-center">
                        <a href="#" class="btn-sm btn-danger post-thumbnail-delete-button" id="thumbnail-{0}">Delete</a>
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
            'slug',
            'description',
            'keywords',
            'content',
            HTML('''
                <div class="row my-4">
                    <div class="col-2"></div>
                    <div class="col-10"><div id="thumbnail-list" class="row">{0}</div></div>
                </div>
            '''.format(thumbnail_section)),
        ]

        if self.categories:
            fieldset.append('category')
            self.fields['category'].required = True

        fieldset += [
            'status',
            'allow_highlight',
            'allow_comments',
            'excerpt',
            'tags',
            'thumbnail',
        ]

        self.helper.layout = Layout(
            Fieldset(*fieldset),
            Div(
                Submit('submit', _('Write'), css_class='btn btn-info'),
                css_class='offset-md-2 col-md-10 submit-padding-left',
            )
        )

    class Meta:
        model = Post
        fields = (
            'title', 'slug', 'description', 'keywords', 'content', 'category',
            'status', 'allow_highlight', 'allow_comments', 'excerpt', 'tags', 'thumbnail', 'owner'
        )
        widgets = {
            'content': PostSummernoteBs4Widget(
                options={
                    'upload_url': blog_settings.BLOG_FILE_UPLOAD_URL,
                    'delete_url': blog_settings.BLOG_FILE_DELETE_URL,
                    'max_upload_size': rakmai_settings.UPLOAD_FILE_MAX_SIZE,
                    'content_types': rakmai_settings.UPLOAD_FILE_CONTENT_TYPES,
                    'file_extensions': rakmai_settings.UPLOAD_FILE_EXTENSIONS,
                }
            ),
        }


class PostAttachmentForm(PostForm):
    attachments = forms.UUIDField(widget=forms.HiddenInput(), required=False)

    def clean_attachments(self):
        data = self.data.getlist('attachments')

        count = self.instance.attachments.count() if self.instance else 0

        if count + len(data) > blog_settings.POST_MAX_FILE_COUNT:
            raise forms.ValidationError(_('Maximum number of files exceeded.'))

        return data


class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        # Admin sets `blog`, `owner`.
        fields = (
            'blog', 'title', 'slug', 'description', 'keywords', 'content', 'category',
            'status', 'allow_comments', 'is_removed', 'excerpt', 'tags', 'thumbnail', 'owner',
        )


class PostSearchForm(forms.Form):
    q = forms.CharField(
        label=_('search word'),
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('search word'),
                'required': 'True',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        q = kwargs.pop('q', '')

        super(PostSearchForm, self).__init__(*args, **kwargs)

        self.fields['q'].initial = q
