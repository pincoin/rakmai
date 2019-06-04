import logging

from django.http import (
    Http404, JsonResponse
)
from django.views.generic import RedirectView
from django.views.generic.edit import FormView

from .forms import (
    UploadAttachmentForm, DeleteAttachmentForm
)
from .helpers import get_sub_domain


class FileUploadView(FormView):
    logger = logging.getLogger(__name__)

    """Provide a way to show and handle uploaded files in a request."""
    form_class = UploadAttachmentForm

    def upload_file(self, *args, **kwargs):
        """Abstract method must be overridden."""
        raise NotImplementedError

    def form_valid(self, form):
        """If the form is valid, return JSON file list after saving them"""
        data = self.upload_file(uploaded_files=self.request.FILES)
        return JsonResponse(data)

    def form_invalid(self, form):
        self.logger.debug(form.errors)

        """If the form is invalid, return HTTP 400 error"""
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class FileDeleteView(FormView):
    """Provide a way to show and handle files to be deleted in a request."""
    form_class = DeleteAttachmentForm

    def delete_file(self, *args, **kwargs):
        """Abstract method must be overridden."""
        raise NotImplementedError

    def form_valid(self, form):
        """If the form is valid, return JSON file list after deleting them"""
        data = self.delete_file(form=form, user=self.request.user)
        return JsonResponse(data)

    def form_invalid(self, form):
        """If the form is invalid, return HTTP 400 error"""
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class HomeView(RedirectView):
    permanent = False
    query_string = True
    pattern_name = 'shop:home'

    def get_redirect_url(self, *args, **kwargs):
        kwargs = {'store': 'default'}

        sub_domain = get_sub_domain(self.request)

        if not sub_domain:
            raise Http404("Page not found")

        if sub_domain == 'card':
            self.pattern_name = 'card:home'

        return super(HomeView, self).get_redirect_url(*args, **kwargs)
