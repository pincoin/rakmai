from celery import shared_task

from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _


@shared_task
def send_feedback_email(subject, message, from_email, recipient):
    send_mail(
        _("You've got feedback. : {}").format(subject),
        message,
        from_email,
        [recipient],
        fail_silently=True,
    )
