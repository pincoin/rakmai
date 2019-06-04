from os.path import splitext

from django import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from . import settings as rakmai_settings


class UploadAttachmentForm(forms.Form):
    files = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'multiple': True}), required=False)

    def clean_files(self):
        content = self.cleaned_data['files']

        if not content:
            raise forms.ValidationError(_('Invalid file type'))

        content_type = content.content_type.split('/')[0]
        extension = splitext(content.name)[1][1:].lower()

        if extension not in rakmai_settings.UPLOAD_FILE_EXTENSIONS \
                or content_type not in rakmai_settings.UPLOAD_FILE_CONTENT_TYPES:
            raise forms.ValidationError(_('File type is not supported'))

        if content.size > rakmai_settings.UPLOAD_FILE_MAX_SIZE:
            raise forms.ValidationError(_('Please keep filesize under {}. Current filesize {}').format(
                filesizeformat(rakmai_settings.UPLOAD_FILE_MAX_SIZE), filesizeformat(content.size)))

        return content


class DeleteAttachmentForm(forms.Form):
    uid = forms.UUIDField()
