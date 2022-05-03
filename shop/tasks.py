import base64

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_notification_email(subject, message, from_email, recipient, html_message=None):
    send_mail(
        subject,
        message,
        from_email,
        recipient,
        fail_silently=True,
        html_message=html_message,
    )


@shared_task
def send_notification_line(message):
    url = 'https://notify-api.line.me/api/notify'
    payload = {'message': message}
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache',
        'Authorization': 'Bearer ' + settings.LINE_NOTIFY_ACCESS_TOKEN,
    }
    requests.post(url, data=payload, headers=headers)


@shared_task
def send_sms(phone, message):
    url = 'https://apis.aligo.in/send/'
    payload = {
        'key': settings.ALIGO_API_KEY,
        'user_id': settings.ALIGO_USER_ID,
        'sender': settings.ALIGO_SENDER,
        'receiver': phone,
        'msg': message
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache',
    }
    requests.post(url, data=payload, headers=headers)


@shared_task
def send_paypal_refund(transaction):
    credentials = "%s:%s" % (settings.PAYPAL['api_client_id'], settings.PAYPAL['api_client_secret'])
    credentials_encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8').replace("\n", "")

    url = '{}/v1/oauth2/token'.format(settings.PAYPAL['api_url'])
    payload = {
        'grant_type': 'client_credentials',
    }
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en_US',
        'Authorization': ('Basic {}'.format(credentials_encoded)),
    }
    response = requests.post(url, data=payload, headers=headers, )

    url = '{}/v2/payments/captures/{}/refund'.format(settings.PAYPAL['api_url'], transaction)
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Authorization': 'Bearer {}'.format(response.json()['access_token']),
    }
    requests.post(url, data=payload, headers=headers)
