from django.conf import settings

# The maximum number of uploaded files
MESSAGE_MAX_FILE_COUNT = getattr(settings, 'MESSAGE_MAX_FILE_COUNT', 10)

# URL for file upload
BOARD_FILE_UPLOAD_URL = getattr(settings, 'BOARD_FILE_UPLOAD_URL', '/board/upload-file')

# URL for file download
BOARD_FILE_DELETE_URL = getattr(settings, 'BOARD_FILE_DELETE_URL', '/board/delete-file')
