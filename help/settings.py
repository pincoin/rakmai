from django.conf import settings

HELP_CHUNK_SIZE = getattr(settings, 'HELP_CHUNK_SIZE', 10)

HELP_BLOCK_SIZE = getattr(settings, 'HELP_BLOCK_SIZE', 10)
