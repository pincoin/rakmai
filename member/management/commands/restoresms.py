from xml.etree.ElementTree import parse

from django.core.management.base import BaseCommand

from member.models import (
    Mms, MmsData
)


class Command(BaseCommand):
    help = 'Restore SMS/MMS'

    def add_arguments(self, parser):
        parser.add_argument('sms.xml', type=str)

    def handle(self, *args, **options):
        tree = parse(options['sms.xml'])

        smses = tree.getroot()
        self.stdout.write('count={}, backup_set={}, backup_date={}'
                          .format(smses.get('count'), smses.get('backup_set'), smses.get('backup_date')))

        """
        # sms backup
        for sms in smses.findall('sms'):
            if sms.get('type') == '1':
                print(sms.attrib['address'], sms.attrib['body'], sms.attrib['date_sent'])
        """

        for m in smses.findall('mms'):
            if m.get('m_type') == '132':
                mms = Mms()
                mms.cellphone = m.get('address')
                mms.sent = m.get('readable_date')
                mms.save()

                for part in m.find('parts').getchildren():
                    data = MmsData()
                    data.mms = mms

                    if part.get('ct') == 'text/plain':
                        data.data = part.get('text')
                        data.mime = MmsData.MIME_CHOICES.txt
                    elif part.get('ct') == 'image/jpeg':
                        data.data = part.get('data')
                        data.mime = MmsData.MIME_CHOICES.jpg
                    elif part.get('ct') == 'image/png':
                        data.data = part.get('data')
                        data.mime = MmsData.MIME_CHOICES.png

                    data.save()

        self.stdout.write(self.style.SUCCESS('Successfully restored SMS and MMS'))
