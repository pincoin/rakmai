from django.conf import settings

# Book Theme
BOOK_THEME = getattr(settings, 'BOOK_THEME', 'default')

# Book Pagination Block Size
BOOK_BLOCK_SIZE = getattr(settings, 'BOOK_BLOCK_SIZE', 10)

# Book Pagination Chunk Size
BOOK_CHUNK_SIZE = getattr(settings, 'BOOK_CHUNK_SIZE', 10)

# The maximum number of uploaded files
PAGE_MAX_FILE_COUNT = getattr(settings, 'PAGE_MAX_FILE_COUNT', 20)

# URL for file upload
BOOK_FILE_UPLOAD_URL = getattr(settings, 'BOOK_FILE_UPLOAD_URL', '/book/upload-file')

# URL for file download
BOOK_FILE_DELETE_URL = getattr(settings, 'BOOK_FILE_DELETE_URL', '/book/delete-file')
