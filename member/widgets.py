from django.forms.widgets import ClearableFileInput


class DocumentClearableFileInput(ClearableFileInput):
    template_name = 'member/account/forms/document_clearable_file_input.html'
